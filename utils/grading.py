"""
Utilities for calculating area grades based on proximity to public transport
"""
import numpy as np
from math import radians, cos, sin, asin, sqrt
import pandas as pd
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Gemini API key from environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth specified in decimal degrees
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km

def find_nearby_transport(osm_data, lat, lon, max_distance=1.0, exclude_types=None, include_unnamed=False, include_stop_positions=False):
    """
    Find transport options within a specified distance (km)
    
    Args:
        osm_data: DataFrame containing the OSM data
        lat, lon: Latitude and longitude of the search point
        max_distance: Maximum distance in kilometers
        exclude_types: List of transport types to exclude (e.g. ['unknown'])
        include_unnamed: Whether to include transport points with no name
        include_stop_positions: Whether to include stop_position nodes
        
    Returns:
        DataFrame of nearby transport options with distances
    """
    # Set default value for exclude_types
    if exclude_types is None:
        exclude_types = []
    
    # Calculate distance for each transport node
    distances = []
    for _, row in osm_data.iterrows():
        # Skip excluded transport types
        if row['transport_type'] in exclude_types:
            continue
            
        # Skip unnamed transport points if specified
        if not include_unnamed and (not row['name'] or str(row['name']).strip() == ''):
            continue
            
        # Skip stop_position nodes if specified
        if not include_stop_positions and row['transport_type'] == 'stop_position':
            continue
            
        distance = haversine(lon, lat, row['lon'], row['lat'])
        if distance <= max_distance:
            distances.append({
                'id': row['id'],
                'type': row['transport_type'],
                'name': row['name'],
                'lat': row['lat'],
                'lon': row['lon'],
                'distance_km': distance
            })
    
    # Convert to DataFrame and sort by distance
    if distances:
        nearby_df = pd.DataFrame(distances)
        return nearby_df.sort_values('distance_km')
    else:
        return pd.DataFrame()

def calculate_transport_scores(nearby_transport):
    """
    Calculate scores for each transport type based on proximity
    
    Args:
        nearby_transport: DataFrame of nearby transport options
        
    Returns:
        dict: Scores for each transport type and overall score
    """
    scores = {
        'bus': 0,
        'tram': 0,
        'velobike': 0
    }
    
    if nearby_transport.empty:
        return {
            'bus_score': 0,
            'tram_score': 0, 
            'velobike_score': 0,
            'overall_score': 0
        }
    
    # Get closest options for each transport type
    for transport_type in ['bus', 'tram', 'velobike', 'bus_stop', 'tram_stop']:
        filtered = nearby_transport[nearby_transport['type'] == transport_type]
        if not filtered.empty:
            closest = filtered.iloc[0]
            distance = closest['distance_km']
            
            # Map bus_stop and tram_stop to bus and tram categories
            if transport_type == 'bus_stop':
                transport_type = 'bus'
            elif transport_type == 'tram_stop':
                transport_type = 'tram'
            
            # Use proximity score for all transport types
            scores[transport_type] = calculate_proximity_score(distance)
    
    # Calculate overall score (weighted average)
    weights = {'bus': 0.4, 'tram': 0.4, 'velobike': 0.2}
    overall_score = sum(scores[t] * weights[t] for t in weights.keys())
    
    # Normalize overall score to a maximum of 100
    overall_score = min(overall_score, 100)
    
    return {
        'bus_score': scores['bus'],
        'tram_score': scores['tram'],
        'velobike_score': scores['velobike'],
        'overall_score': overall_score
    }

def calculate_proximity_score(distance_km):
    """
    Calculate a score (0-100) based on distance to transport option.
    Starts from 100 and decreases as distance increases.
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        int: Score from 0-100
    """
    if distance_km < 0.1:  # Very close (under 100m)
        return 100
    elif distance_km < 0.25:  # Under 250m
        return 90
    elif distance_km < 0.5:  # Under 500m
        return 80
    elif distance_km < 0.75:  # Under 750m
        return 70
    elif distance_km < 1.0:  # Under 1km
        return 60
    else:
        return 0  # Too far

def calculate_area_grade(osm_data, lat, lon, exclude_types=None, include_unnamed=False, include_stop_positions=False):
    """
    Calculate the area grade for a location based on transport proximity
    
    Args:
        osm_data: DataFrame containing the OSM data
        lat, lon: Latitude and longitude of the location
        exclude_types: List of transport types to exclude (e.g. ['unknown'])
        include_unnamed: Whether to include transport points with no name
        include_stop_positions: Whether to include stop_position nodes
        
    Returns:
        dict: Grade results including scores and letter grade
    """
    # Find nearby transport options
    nearby = find_nearby_transport(
        osm_data, 
        lat, 
        lon, 
        exclude_types=exclude_types,
        include_unnamed=include_unnamed,
        include_stop_positions=include_stop_positions
    )
    
    # Calculate scores
    scores = calculate_transport_scores(nearby)
    
    # Convert overall score to letter grade
    overall_score = scores['overall_score']
    if overall_score >= 90:
        letter_grade = 'A+'
    elif overall_score >= 85:
        letter_grade = 'A'
    elif overall_score >= 80:
        letter_grade = 'A-'
    elif overall_score >= 75:
        letter_grade = 'B+'
    elif overall_score >= 70:
        letter_grade = 'B'
    elif overall_score >= 65:
        letter_grade = 'B-'
    elif overall_score >= 60:
        letter_grade = 'C+'
    elif overall_score >= 50:
        letter_grade = 'C'
    elif overall_score >= 40:
        letter_grade = 'C-'
    elif overall_score >= 30:
        letter_grade = 'D'
    else:
        letter_grade = 'F'
    
    # Create nearby transport list for the results
    nearby_transport = []
    if not nearby.empty:
        for _, row in nearby.iterrows():
            nearby_transport.append({
                'type': row['type'],
                'name': row['name'],
                'distance_km': round(row['distance_km'], 3),
                'lat': row['lat'],
                'lon': row['lon']
            })
    
    return {
        'bus_score': scores['bus_score'],
        'tram_score': scores['tram_score'],
        'velobike_score': scores['velobike_score'],
        'overall_score': round(scores['overall_score'], 1),
        'overall_grade': letter_grade,
        'nearby_transport': nearby_transport
    } 