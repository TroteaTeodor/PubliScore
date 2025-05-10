from flask import Flask, render_template, request, jsonify
from app.utils.data_loader import load_osm_data
from app.models.scoring import calculate_accessibility_score, find_transport_nodes
from app.utils.gemini_utils import generate_location_description
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
        
        # Generate location description using Gemini API
        location_description = generate_location_description(lat, lon, details)
        
        # Prepare response
        response_data = {
            'score': score,
            'details': details,
            'transport_nodes': nearby_nodes.to_dict('records') if not nearby_nodes.empty else [],
            'location_description': location_description
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_score: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/all_transport_nodes')
def get_all_transport_nodes():
    """API endpoint to get all transport nodes for the heatmap"""
    try:
        # Check if data is loaded
        if osm_data is None or osm_data.empty:
            logger.warning("OSM data not loaded, attempting to load")
            if not load_data():
                logger.error("Failed to load OSM data")
                return jsonify({'error': 'Data not loaded yet'}), 503
        
        # Filter for relevant transport nodes
        transport_nodes = osm_data[
            (osm_data['transport_type'] == 'bus_stop') |
            (osm_data['transport_type'] == 'tram_stop') |
            (osm_data['transport_type'] == 'velo_station')
        ]
        
        # Log the data types and sample data
        logger.debug(f"Transport nodes data types:\n{transport_nodes.dtypes}")
        logger.debug(f"Sample data:\n{transport_nodes.head()}")
        
        # Convert to list of dictionaries and ensure all values are JSON serializable
        nodes_list = []
        for _, row in transport_nodes.iterrows():
            try:
                # Ensure all values are properly converted
                lat = float(row['lat'])
                lon = float(row['lon'])
                transport_type = str(row['transport_type'])
                
                # Validate the values
                if not (0 <= lat <= 90 and -180 <= lon <= 180):
                    logger.warning(f"Invalid coordinates: lat={lat}, lon={lon}")
                    continue
                    
                if transport_type not in ['bus_stop', 'tram_stop', 'velo_station']:
                    logger.warning(f"Invalid transport type: {transport_type}")
                    continue
                
                node = {
                    'lat': lat,
                    'lon': lon,
                    'transport_type': transport_type
                }
                nodes_list.append(node)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing row: {row}, Error: {e}")
                continue
        
        logger.debug(f"Processed {len(nodes_list)} valid nodes")
        
        # Test JSON serialization
        try:
            import json
            test_json = json.dumps({'transport_nodes': nodes_list})
            logger.debug("JSON serialization successful")
        except Exception as e:
            logger.error(f"JSON serialization failed: {e}")
            return jsonify({'error': 'Data serialization failed'}), 500
        
        return jsonify({'transport_nodes': nodes_list})
        
    except Exception as e:
        logger.error(f"Error in get_all_transport_nodes: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Load data at startup
    if not load_data():
        logger.warning("Failed to load initial data")
    app.run(host='0.0.0.0', port=5000, debug=True) 