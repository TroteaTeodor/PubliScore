import pandas as pd
import requests
import zipfile
import io
import logging
from functools import lru_cache
from flask import Flask, jsonify
from geopy.distance import geodesic

app = Flask(__name__, static_folder='static')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def download_gtfs_data():
    """Download De Lijn GTFS data"""
    try:
        # De Lijn GTFS feed URL
        url = "http://gtfs.irail.be/de-lijn/de_lijn-gtfs.zip"
        logger.info("Downloading GTFS data from De Lijn...")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.info("GTFS data downloaded successfully")
        return zipfile.ZipFile(io.BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading GTFS data: {e}")
        return None

@lru_cache(maxsize=1)
def load_gtfs_files():
    """Load the GTFS files into memory"""
    gtfs_zip = download_gtfs_data()
    if not gtfs_zip:
        return {}

    try:
        return {
            'routes': pd.read_csv(gtfs_zip.open('routes.txt')).drop_duplicates(),
            'stops': pd.read_csv(gtfs_zip.open('stops.txt')).drop_duplicates(),
        }
    except Exception as e:
        logger.error(f"Error reading GTFS files: {e}")
        return {}

def load_gtfs_routes():
    """Load and process GTFS routes and stops data."""
    gtfs_data = load_gtfs_files()
    if not gtfs_data:
        return pd.DataFrame(), pd.DataFrame()

    try:
        routes_df = gtfs_data['routes']
        stops_df = gtfs_data['stops']

        logger.info(f"Loaded {len(routes_df)} routes and {len(stops_df)} stops.")

        # Filter and process routes and stops
        route_type_map = {
            '0': 'tram', '1': 'metro', '2': 'rail', '3': 'bus', '4': 'ferry',
            '5': 'cable_tram', '6': 'aerial_lift', '7': 'funicular',
            '11': 'trolleybus', '12': 'monorail'
        }
        routes_df['route_type_name'] = routes_df['route_type'].astype(str).map(route_type_map)

        logger.info(f"Processed {len(routes_df)} routes.")
        return routes_df, stops_df

    except Exception as e:
        logger.error(f"Error processing GTFS routes and stops: {e}")
        return pd.DataFrame(), pd.DataFrame()

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
        routes_df, stops_df = load_gtfs_routes()
        if routes_df.empty or stops_df.empty:
            logger.debug("No routes or stops found.")
            return []

        # Convert radius to degrees (approximate)
        radius_deg = radius_km / 111.0
        logger.debug(f"Radius in degrees: {radius_deg}")

        # Find stops within radius
        nearby_stops = stops_df[
            (stops_df['stop_lat'].between(lat - radius_deg, lat + radius_deg)) &
            (stops_df['stop_lon'].between(lon - radius_deg, lon + radius_deg))
        ]
        
        logger.debug(f"Found {len(nearby_stops)} nearby stops within radius.")

        if nearby_stops.empty:
            logger.debug("No nearby stops found within the radius.")
            return []
        
        # Group by route to get unique routes
        routes = []
        for route_id, route_group in nearby_stops.groupby('route_id'):
            route = route_group.iloc[0]
            logger.debug(f"Processing route {route_id} with {len(route_group)} stops.")

            routes.append({
                'route_id': route_id,
                'route_type': route['route_type_name'],
                'route_short_name': route['route_short_name'],
                'route_long_name': route['route_long_name'],
                'stops': route_group[['stop_lat', 'stop_lon', 'stop_name', 'stop_sequence']].to_dict('records')
            })
        
        logger.debug(f"Returning {len(routes)} routes for the given stop.")
        return routes
        
    except Exception as e:
        logger.error(f"Error getting route info for stop: {e}")
        return [] 

def is_within_antwerp(lat, lon):
    """Check if the coordinates are within the bounds of Antwerp."""
    return 51.16 <= lat <= 51.31 and 4.3 <= lon <= 4.5

def get_routes_with_shapes(lat=None, lon=None, radius_km=0.1):
    """Get routes with shapes, optionally filtered by latitude and longitude."""
    gtfs = load_gtfs_files()
    if not gtfs:
        logger.error("GTFS data could not be loaded")
        return []

    try:
        logger.debug(f"Getting routes with shapes for lat={lat}, lon={lon}, radius={radius_km}km")

        routes = gtfs['routes']
        stops = gtfs['stops']
        logger.info(f"Loaded {len(routes)} routes and {len(stops)} stops")

        # Filter to only include Antwerp routes (if needed)
        routes = routes[routes['route_id'].apply(lambda route_id: is_within_antwerp_route(route_id, lat, lon, radius_km))]

        logger.debug(f"After filtering for Antwerp routes, found {len(routes)} routes.")

        results = []

        for route_id, route in routes.iterrows():
            # Collect the route information and stops
            route_info = {
                'route_id': route['route_id'],
                'route_type': route['route_type_name'],
                'route_short_name': route['route_short_name'],
                'route_long_name': route['route_long_name'],
                'stops': stops[stops['route_id'] == route['route_id']][['stop_lat', 'stop_lon', 'stop_name']].to_dict('records')
            }
            results.append(route_info)

        logger.info(f"Found {len(results)} routes")
        return results

    except Exception as e:
        logger.error(f"Error in get_routes_with_shapes: {e}")
        return []

def is_within_radius(lat1, lon1, lat2, lon2, radius_km):
    """Check if the coordinates (lat2, lon2) are within a given radius (in km) of the coordinates (lat1, lon1)."""
    return geodesic((lat1, lon1), (lat2, lon2)).km <= radius_km

def is_within_antwerp_route(route_id, lat, lon, radius_km):
    """Check if a route has stops within Antwerp and the radius."""
    stops = get_stops_for_route(route_id)
    for stop in stops:
        stop_lat, stop_lon = stop['lat'], stop['lon']
        if is_within_antwerp(stop_lat, stop_lon) and is_within_radius(lat, lon, stop_lat, stop_lon, radius_km):
            return True
    return False

def get_stops_for_route(route_id):
    """Get all stops for a given route_id from globally cached GTFS data."""
    gtfs_data = load_gtfs_files()
    if not gtfs_data:
        logger.error("GTFS data could not be loaded.")
        return []

    try:
        stop_times_df = gtfs_data['stop_times']
        stops_df = gtfs_data['stops']
        trips_df = gtfs_data.get('trips', pd.DataFrame())

        # Find all trips for this route if trips data is available
        if not trips_df.empty:
            trip_ids = trips_df[trips_df['route_id'] == route_id]['trip_id'].unique()
            stop_times = stop_times_df[stop_times_df['trip_id'].isin(trip_ids)]
            stop_ids = stop_times['stop_id'].unique()
        else:
            stop_ids = stop_times_df[stop_times_df['route_id'] == route_id]['stop_id'].unique()

        # Get stop info
        stops = stops_df[stops_df['stop_id'].isin(stop_ids)]

        return stops[['stop_lat', 'stop_lon']].rename(columns={'stop_lat': 'lat', 'stop_lon': 'lon'}).to_dict('records')

    except Exception as e:
        logger.error(f"Error in get_stops_for_route({route_id}): {e}")
        return []
