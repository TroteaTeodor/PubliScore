import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from typing import Tuple, Dict, Any

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = 6371 * c
    
    return distance

def find_transport_nodes(df: pd.DataFrame, lat: float, lon: float, radius_km: float = 1.0) -> pd.DataFrame:
    """
    Find all transport nodes within a given radius of a location.
    
    Args:
        df (pd.DataFrame): DataFrame containing transport nodes
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        radius_km (float): Search radius in kilometers
        
    Returns:
        pd.DataFrame: Transport nodes within the radius
    """
    if df is None or df.empty:
        return pd.DataFrame()
        
    radius_deg = radius_km / 111.0  # 1 degree ≈ 111 km
    
    mask = (
        (df['lat'].between(lat - radius_deg, lat + radius_deg)) &
        (df['lon'].between(lon - radius_deg, lon + radius_deg))
    )
    nearby_df = df[mask].copy()
    
    if nearby_df.empty:
        return nearby_df
    
    nearby_df['distance'] = np.sqrt(
        ((nearby_df['lat'] - lat) * 111.0)**2 +
        ((nearby_df['lon'] - lon) * 111.0 * np.cos(np.radians(lat)))**2
    )
    
    return nearby_df[nearby_df['distance'] <= radius_km]

def calculate_accessibility_score(df: pd.DataFrame, lat: float, lon: float, radius_km: float = 1.0) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate the accessibility score for a location based on nearby transport options.
    
    Args:
        df (pd.DataFrame): DataFrame containing transport nodes
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        radius_km (float): Search radius in kilometers
        
    Returns:
        Tuple[float, Dict[str, Any]]: Score (0-10) and details about nearby transport
    """
    if df is None or df.empty:
        return 0.0, {
            'bus_stops': 0,
            'tram_stops': 0,
            'velo_stations': 0,
            'closest_bus': None,
            'closest_tram': None,
            'closest_velo': None
        }
    
    nearby = find_transport_nodes(df, lat, lon, radius_km)
    
    if nearby.empty:
        return 0.0, {
            'bus_stops': 0,
            'tram_stops': 0,
            'velo_stations': 0,
            'closest_bus': None,
            'closest_tram': None,
            'closest_velo': None
        }
    
    type_counts = nearby['transport_type'].value_counts()
    bus_stops = int(type_counts.get('bus_stop', 0))
    tram_stops = int(type_counts.get('tram_stop', 0))
    velo_stations = int(type_counts.get('velo_station', 0))
    
    closest_bus = float('inf')
    closest_tram = float('inf')
    closest_velo = float('inf')
    
    for _, node in nearby.iterrows():
        distance = haversine_distance(lat, lon, node['lat'], node['lon'])
        if node['transport_type'] == 'bus_stop':
            closest_bus = min(closest_bus, distance)
        elif node['transport_type'] == 'tram_stop':
            closest_tram = min(closest_tram, distance)
        elif node['transport_type'] == 'velo_station':
            closest_velo = min(closest_velo, distance)
    
    bus_score = 0.0
    if bus_stops > 0:
        bus_score = min(3.0, bus_stops * 0.4)
        if closest_bus < float('inf'):
            bus_score *= float(np.exp(-2 * closest_bus / radius_km))
    
    tram_score = 0.0
    if tram_stops > 0:
        tram_score = min(4.0, tram_stops * 1.0)
        if closest_tram < float('inf'):
            tram_score *= float(np.exp(-2 * closest_tram / radius_km))
    
    velo_score = 0.0
    if velo_stations > 0:
        velo_score = min(3.0, velo_stations * 0.6)
        if closest_velo < float('inf'):
            velo_score *= float(np.exp(-2 * closest_velo / radius_km))
    
    total_score = float(min(10.0, bus_score + tram_score + velo_score))
    
    details = {
        'bus_stops': bus_stops,
        'tram_stops': tram_stops,
        'velo_stations': velo_stations,
        'closest_bus': float(closest_bus) if closest_bus < float('inf') else None,
        'closest_tram': float(closest_tram) if closest_tram < float('inf') else None,
        'closest_velo': float(closest_velo) if closest_velo < float('inf') else None
    }
    
    return total_score, details 