"""
Data loading utilities for the Antwerp OSM Navigator dataset
"""
import pandas as pd
from datasets import load_dataset
import re
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    r = 6371  # Radius of earth in kilometers
    return c * r * 1000  # Convert to meters

def remove_duplicate_velo_stations(df, radius=100):
    """
    Remove velo stations that are within radius meters of each other.
    Keep only one station per radius.
    """
    # Get only velo stations
    velo_mask = df['transport_type'] == 'velobike'
    velo_stations = df[velo_mask].copy()
    other_stations = df[~velo_mask].copy()
    
    if len(velo_stations) == 0:
        return df
    
    # Create a list to store stations to keep
    stations_to_keep = []
    stations_to_remove = set()
    
    # For each velo station
    for i, (idx1, row1) in enumerate(velo_stations.iterrows()):
        if idx1 in stations_to_remove:
            continue
            
        # Check distance with all other velo stations
        for idx2, row2 in velo_stations.iloc[i+1:].iterrows():
            if idx2 in stations_to_remove:
                continue
                
            # Calculate distance
            distance = haversine_distance(
                row1['lat'], row1['lon'],
                row2['lat'], row2['lon']
            )
            
            # If within radius, mark for removal
            if distance < radius:
                stations_to_remove.add(idx2)
        
        # If this station wasn't marked for removal, keep it
        if idx1 not in stations_to_remove:
            stations_to_keep.append(idx1)
    
    # Combine kept velo stations with other stations
    result = pd.concat([
        velo_stations.loc[stations_to_keep],
        other_stations
    ])
    
    return result

def load_osm_data(dataset_name="ns2agi/antwerp-osm-navigator"):
    """
    Load the Antwerp OSM Navigator dataset from Hugging Face,
    filter for transportation-related data, and return a pandas DataFrame.
    
    Args:
        dataset_name (str): Hugging Face dataset name
        
    Returns:
        pandas.DataFrame: Processed OSM data
    """
    print(f"Loading dataset: {dataset_name}")
    dataset = load_dataset(dataset_name)
    
    # Get the training split
    train_split = dataset["train"]
    
    # Transport-related tags
    transport_tags = [
        "highway", "railway", "bus", "tram", "subway", 
        "bicycle", "amenity", "public_transport", "velo",
        "route", "ref", "network"
    ]
    
    # More specific transport values for better identification
    bus_values = ["bus", "bus_stop", "bus_station"]
    tram_values = ["tram", "tram_stop", "tram_station"]
    velobike_values = ["bicycle", "bicycle_rental", "bicycle_parking", "velo"]
    
    # Filter nodes with transport-related tags
    def has_transport_tags(example):
        if example["type"] != "node":
            return False
        
        # Convert string representation of tags to a dictionary
        tags = eval(example["tags"]) if isinstance(example["tags"], str) else example["tags"]
        
        if not tags:
            return False
            
        # Check if any transport-related tag exists
        for tag in transport_tags:
            if any(tag in key for key in tags.keys()):
                return True
        return False
    
    # Filter the dataset
    transport_nodes = train_split.filter(has_transport_tags)
    
    # Convert to pandas DataFrame
    df = transport_nodes.to_pandas()
    
    # Process tags to extract transport type with more detailed checks
    def extract_transport_type(tags_dict):
        # Direct public_transport tag
        if "public_transport" in tags_dict:
            pt_value = tags_dict["public_transport"]
            # Further classify stop_position and platform
            if pt_value == "stop_position" or pt_value == "platform":
                # Try to determine if it's bus or tram
                for key, value in tags_dict.items():
                    if isinstance(value, str) and any(val in value.lower() for val in bus_values):
                        return "bus"
                    if isinstance(value, str) and any(val in value.lower() for val in tram_values):
                        return "tram"
            return pt_value
            
        # Direct highway matches for bus/tram stops
        if "highway" in tags_dict and tags_dict["highway"] in ["bus_stop", "tram_stop"]:
            return tags_dict["highway"]
            
        # Direct amenity matches for bicycle facilities
        if "amenity" in tags_dict and tags_dict["amenity"] == "bicycle_rental":
            return "velobike"
            
        # Route type
        if "route" in tags_dict:
            route_type = tags_dict["route"]
            if route_type == "bus":
                return "bus_route"
            if route_type == "tram":
                return "tram_route"
                
        # Check for name hints
        if "name" in tags_dict and isinstance(tags_dict["name"], str):
            name = tags_dict["name"].lower()
            if any(re.search(r'\b' + re.escape(bus) + r'\b', name) for bus in bus_values):
                return "bus"
            if any(re.search(r'\b' + re.escape(tram) + r'\b', name) for tram in tram_values):
                return "tram"
            if any(re.search(r'\b' + re.escape(bike) + r'\b', name) for bike in velobike_values):
                return "velobike"
            if "velo" in name:
                return "velobike"
                
        # Check for other transport indicators in any tag
        for key, value in tags_dict.items():
            if isinstance(value, str):
                value_lower = value.lower()
                
                # Bus indicators
                for bus_term in bus_values:
                    if bus_term in key.lower() or bus_term in value_lower:
                        return "bus"
                
                # Tram indicators
                for tram_term in tram_values:
                    if tram_term in key.lower() or tram_term in value_lower:
                        return "tram"
                
                # Bicycle/velobike indicators
                for bike_term in velobike_values:
                    if bike_term in key.lower() or bike_term in value_lower:
                        return "velobike"
        
        return "unknown"
    
    # Extract transport types
    df["transport_type"] = df["tags"].apply(
        lambda x: extract_transport_type(eval(x) if isinstance(x, str) else x)
    )
    
    # Extract name and additional information
    def extract_info(tags_dict):
        info = {
            'name': '',
            'ref': '',
            'network': '',
            'route_ref': '',
            'description': ''
        }
        
        if "name" in tags_dict:
            info['name'] = tags_dict["name"]
        if "ref" in tags_dict:
            info['ref'] = tags_dict["ref"]
        if "network" in tags_dict:
            info['network'] = tags_dict["network"]
        if "route_ref" in tags_dict:
            info['route_ref'] = tags_dict["route_ref"]
        if "description" in tags_dict:
            info['description'] = tags_dict["description"]
            
        return info
    
    # Extract additional information
    info_df = df["tags"].apply(
        lambda x: pd.Series(extract_info(eval(x) if isinstance(x, str) else x))
    )
    df = pd.concat([df, info_df], axis=1)
    
    # Filter out unnamed velobike stations using boolean masks
    # First, identify velobike stations
    velo_mask = df['transport_type'] == 'velobike'
    
    # For velobike stations, check name and ref
    name_mask = df['name'].notna() & \
                ~df['name'].str.lower().isin(['velo', 'velo station', 'bicycle', 'bicycle station']) & \
                ~df['name'].str.lower().str.startswith('velo ') & \
                ~df['name'].str.lower().str.startswith('bicycle ')
    
    ref_mask = df['ref'].notna() & \
               (df['ref'].str.isdigit() | \
               df['ref'].str.contains('station', case=False) | \
               df['ref'].str.contains('st', case=False))
    
    # Keep non-velo stations or velo stations with valid name/ref
    valid_mask = ~velo_mask | (velo_mask & (name_mask | ref_mask))
    
    # Apply the filter
    df = df[valid_mask]
    
    # Remove duplicate velo stations
    df = remove_duplicate_velo_stations(df)
    
    print(f"Loaded {len(df)} transport-related nodes")
    
    return df 