from flask import Flask, render_template, request, jsonify
from app.utils.data_loader import load_osm_data
from app.models.scoring import calculate_accessibility_score, find_transport_nodes
import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__,
           template_folder='app/templates',
           static_folder='app/static')

# Initialize osm_data as None
osm_data = None

def load_data():
    """Load the OSM data when the application starts"""
    global osm_data
    try:
        osm_data = load_osm_data()
        if osm_data is None or osm_data.empty:
            logger.warning("No data loaded")
            return False
        else:
            logger.info(f"Successfully loaded {len(osm_data)} transport nodes")
            return True
    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        osm_data = None
        return False

@app.route('/')
def home():
    """Home page with information about the project"""
    return render_template('home.html')

@app.route('/team')
def team():
    """Page with team information"""
    return render_template('team.html')

@app.route('/search')
def search():
    """Search page for address lookup"""
    return render_template('search.html')

@app.route('/api/score')
def get_score():
    """API endpoint to get the accessibility score for a location"""
    try:
        # Get and validate parameters
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radius = request.args.get('radius', '1.0')
        
        logger.debug(f"Received request with lat={lat}, lon={lon}, radius={radius}")
        
        # Convert parameters to float
        try:
            lat = float(lat)
            lon = float(lon)
            radius = float(radius)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter values: {e}")
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        # Validate coordinate ranges
        if not (0 <= lat <= 90 and -180 <= lon <= 180):
            logger.error(f"Coordinates out of range: lat={lat}, lon={lon}")
            return jsonify({'error': 'Coordinates out of range'}), 400
            
        # Validate radius
        if not (0.1 <= radius <= 5.0):
            logger.error(f"Radius out of range: {radius}")
            return jsonify({'error': 'Radius must be between 0.1 and 5.0 km'}), 400
        
        # Check if data is loaded
        if osm_data is None or osm_data.empty:
            logger.warning("OSM data not loaded, attempting to load")
            if not load_data():
                logger.error("Failed to load OSM data")
                return jsonify({'error': 'Data not loaded yet'}), 503
        
        # Log data state
        logger.debug(f"OSM data shape: {osm_data.shape}")
        logger.debug(f"OSM data columns: {osm_data.columns}")
        logger.debug(f"OSM data types: {osm_data.dtypes}")
        
        # Calculate score
        logger.debug("Calculating score")
        score, details = calculate_accessibility_score(osm_data, lat, lon, radius)
        
        # Get nearby transport nodes for map display
        nearby_nodes = find_transport_nodes(osm_data, lat, lon, radius)
        
        # Convert nearby nodes to list of dictionaries for the response
        transport_nodes = []
        if not nearby_nodes.empty:
            for _, node in nearby_nodes.iterrows():
                node_dict = {
                    'id': int(node['id']),  # Convert numpy.int64 to Python int
                    'lat': float(node['lat']),  # Convert numpy.float64 to Python float
                    'lon': float(node['lon']),  # Convert numpy.float64 to Python float
                    'transport_type': str(node['transport_type']),  # Convert to string
                    'distance': float(node['distance'])  # Convert numpy.float64 to Python float
                }
                
                # Add route information if available
                if 'route_info' in node and node['route_info']:
                    node_dict['route_info'] = node['route_info']
                
                transport_nodes.append(node_dict)
        
        # Convert score and details to Python native types
        response = {
            'score': float(score),  # Convert numpy.float64 to Python float
            'details': {
                'bus_stops': int(details['bus_stops']),  # Convert numpy.int64 to Python int
                'tram_stops': int(details['tram_stops']),
                'velo_stations': int(details['velo_stations']),
                'closest_bus': float(details['closest_bus']) if details['closest_bus'] is not None else None,
                'closest_tram': float(details['closest_tram']) if details['closest_tram'] is not None else None,
                'closest_velo': float(details['closest_velo']) if details['closest_velo'] is not None else None
            },
            'transport_nodes': transport_nodes
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Load data at startup
    if not load_data():
        logger.warning("Failed to load initial data")
    app.run(host='0.0.0.0', port=5000, debug=True) 