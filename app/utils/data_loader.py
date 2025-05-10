import pandas as pd
from datasets import load_dataset
import numpy as np
from functools import lru_cache
import json
import ast
import logging
from .gtfs_loader import get_route_info_for_stop

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def load_osm_data(dataset_name="ns2agi/antwerp-osm-navigator"):
    """
    Load the Antwerp OSM Navigator dataset from HuggingFace
    and process it for use in our application.
    
    Args:
        dataset_name (str): The name of the dataset on HuggingFace
        
    Returns:
        pd.DataFrame: The processed dataset with transport nodes and routes
    """
    try:
        logger.info(f"Loading dataset: {dataset_name}")
        dataset = load_dataset(dataset_name)
        logger.info(f"Dataset loaded successfully. Available splits: {list(dataset.keys())}")
        
        train_split = dataset["train"]
        logger.info(f"Training split size: {len(train_split)}")
        
        df = train_split.to_pandas()
        logger.info(f"DataFrame created with shape: {df.shape}")
        
        def parse_tags(tags_str):
            try:
                if isinstance(tags_str, dict):
                    return tags_str
                if isinstance(tags_str, str):
                    if tags_str == '{}':
                        return {}
                    try:
                        tags_str = tags_str.replace("'", '"')
                        return json.loads(tags_str)
                    except:
                        try:
                            return ast.literal_eval(tags_str)
                        except:
                            try:
                                tags_str = tags_str.strip('{}')
                                pairs = [pair.split(':') for pair in tags_str.split(',')]
                                return {k.strip().strip('"\'').strip(): v.strip().strip('"\'').strip() 
                                        for k, v in pairs if ':' in pair}
                            except:
                                logger.warning(f"Failed to parse tags: {tags_str}")
                                return {}
                return {}
            except Exception as e:
                logger.warning(f"Error parsing tags: {e}")
                return {}
        
        df = df[df['tags'] != '{}']
        logger.info(f"Number of nodes with non-empty tags: {len(df)}")
        
        df['tags'] = df['tags'].apply(parse_tags)
        
        def check_tags(tags):
            if not isinstance(tags, dict):
                logger.debug(f"Tags is not a dictionary: {type(tags)}")
                return False
            
            if tags and len(tags) > 0:
                logger.debug(f"Checking tags: {tags}")
            
            is_transport = (
                'public_transport' in tags or
                (tags.get('highway') == 'bus_stop') or
                (tags.get('railway') in ['tram_stop', 'station', 'halt']) or
                (tags.get('amenity') == 'bicycle_rental') or
                any('velo' in str(v).lower() for v in tags.values()) or
                (tags.get('route') in ['bus', 'tram']) or
                (tags.get('public_transport') == 'stop_position')
            )
            
            if is_transport:
                logger.debug(f"Found transport node with tags: {tags}")
            
            return is_transport
        
        is_transport = df['tags'].apply(check_tags)
        transport_df = df[is_transport].copy()
        
        def get_transport_type(tags):
            if not isinstance(tags, dict):
                return 'unknown'
            
            if tags.get('amenity') == 'bicycle_rental' or any('velo' in str(v).lower() for v in tags.values()):
                return 'velo_station'
            if tags.get('railway') in ['tram_stop', 'station', 'halt'] or tags.get('route') == 'tram':
                return 'tram_stop'
            if tags.get('highway') == 'bus_stop' or tags.get('route') == 'bus':
                return 'bus_stop'
            return 'other'
        
        transport_df['transport_type'] = transport_df['tags'].apply(get_transport_type)
        
        logger.info("Adding GTFS route information...")
        transport_df['route_info'] = transport_df.apply(
            lambda row: get_route_info_for_stop(row['lat'], row['lon']) if row['transport_type'] in ['bus_stop', 'tram_stop'] else None,
            axis=1
        )
        
        transport_df = transport_df[['id', 'lat', 'lon', 'transport_type', 'route_info']]
        
        logger.info(f"\nLoaded {len(transport_df)} public transport nodes:")
        logger.info(transport_df['transport_type'].value_counts())
        
        return transport_df
    
    except Exception as e:
        logger.error(f"Error loading dataset: {e}", exc_info=True)
        return pd.DataFrame()

def is_transport_node(tags):
    """
    Check if a node represents a public transport stop or station.
    
    Args:
        tags (dict): Dictionary of OSM tags
        
    Returns:
        bool: True if the node is a transport stop/station
    """
    if not isinstance(tags, dict):
        logger.warning(f"Tags is not a dictionary: {type(tags)}")
        return False
        
    if tags.get('highway') == 'bus_stop' or tags.get('route') == 'bus':
        return True
        
    if tags.get('railway') == 'tram_stop' or tags.get('route') == 'tram':
        return True
        
    if tags.get('amenity') == 'bicycle_rental':
        return True
        
    return False

def classify_transport_type(tags):
    """
    Classify the type of transport node.
    
    Args:
        tags (dict): Dictionary of OSM tags
        
    Returns:
        str: Transport type ('bus_stop', 'tram_stop', 'velo_station', or None)
    """
    if not isinstance(tags, dict):
        return None
        
    if tags.get('highway') == 'bus_stop' or tags.get('route') == 'bus':
        return 'bus_stop'
    elif tags.get('railway') == 'tram_stop' or tags.get('route') == 'tram':
        return 'tram_stop'
    elif tags.get('amenity') == 'bicycle_rental':
        return 'velo_station'
    return None 