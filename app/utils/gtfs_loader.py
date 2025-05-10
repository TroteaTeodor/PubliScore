import pandas as pd
from pathlib import Path
import requests
import zipfile
import io
import logging
from functools import lru_cache

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def download_gtfs_data():
    """Download De Lijn GTFS data"""
    try:
        url = "https://www.delijn.be/gtfs/gtfs.zip"
        logger.info("Downloading GTFS data from De Lijn...")
        response = requests.get(url)
        response.raise_for_status()
        logger.info("GTFS data downloaded successfully")
        return zipfile.ZipFile(io.BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading GTFS data: {e}")
        return None

@lru_cache(maxsize=1)
def load_gtfs_routes():
    """Load and process GTFS routes data"""
    try:
        gtfs_zip = download_gtfs_data()
        if gtfs_zip is None:
            return pd.DataFrame()
        
        logger.info("Loading GTFS files...")
        
        routes_df = pd.read_csv(gtfs_zip.open('routes.txt'))
        trips_df = pd.read_csv(gtfs_zip.open('trips.txt'))
        stop_times_df = pd.read_csv(gtfs_zip.open('stop_times.txt'))
        stops_df = pd.read_csv(gtfs_zip.open('stops.txt'))
        
        logger.info(f"Loaded {len(routes_df)} routes, {len(trips_df)} trips, {len(stops_df)} stops")
        
        route_info = pd.merge(
            pd.merge(
                routes_df,
                trips_df,
                on='route_id'
            ),
            pd.merge(
                stop_times_df,
                stops_df,
                on='stop_id'
            ),
            on='trip_id'
        )
        
        route_info = route_info.sort_values(['trip_id', 'stop_sequence'])
        
        route_type_map = {
            '0': 'tram',
            '1': 'metro',
            '2': 'rail',
            '3': 'bus',
            '4': 'ferry',
            '5': 'cable_tram',
            '6': 'aerial_lift',
            '7': 'funicular',
            '11': 'trolleybus',
            '12': 'monorail'
        }
        route_info['route_type_name'] = route_info['route_type'].astype(str).map(route_type_map)
        
        route_info['display_type'] = route_info['route_type_name'].apply(lambda x: 'tram' if x in ['tram', 'cable_tram'] else 'bus')
        
        logger.info(f"Processed {len(route_info)} route segments")
        return route_info
        
    except Exception as e:
        logger.error(f"Error loading GTFS data: {e}")
        return pd.DataFrame()

def get_route_info_for_stop(lat, lon, radius_km=0.1):
    """
    Get route information for a stop at the given coordinates
    
    Args:
        lat (float): Latitude of the stop
        lon (float): Longitude of the stop
        radius_km (float): Search radius in kilometers
        
    Returns:
        list: List of route information dictionaries
    """
    try:
        route_info = load_gtfs_routes()
        if route_info.empty:
            return []
        
        radius_deg = radius_km / 111.0
        
        nearby_stops = route_info[
            (route_info['stop_lat'].between(lat - radius_deg, lat + radius_deg)) &
            (route_info['stop_lon'].between(lon - radius_deg, lon + radius_deg))
        ]
        
        if nearby_stops.empty:
            return []
        
        routes = []
        for route_id, route_group in nearby_stops.groupby('route_id'):
            route = route_group.iloc[0]
            routes.append({
                'route_id': route_id,
                'route_type': route['route_type_name'],
                'route_short_name': route['route_short_name'],
                'route_long_name': route['route_long_name'],
                'stops': route_group[['stop_lat', 'stop_lon', 'stop_name', 'stop_sequence']].to_dict('records')
            })
        
        return routes
        
    except Exception as e:
        logger.error(f"Error getting route info for stop: {e}")
        return [] 