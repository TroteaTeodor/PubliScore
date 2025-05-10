from flask import Flask, render_template, request, jsonify
from app.utils.data_loader import load_osm_data
from app.models.scoring import calculate_accessibility_score, find_transport_nodes
from app.utils.gemini_utils import generate_location_description
import os
import pandas as pd
import logging
import requests
import json
import math
from geopy.distance import geodesic

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

@app.route('/api/recommendations')
def get_recommendations():
    """API endpoint to get Gemini-generated location recommendations"""
    try:
        # Check if data is loaded
        if osm_data is None or osm_data.empty:
            logger.warning("OSM data not loaded, attempting to load")
            if not load_data():
                logger.error("Failed to load OSM data")
                return jsonify({'error': 'Data not loaded yet'}), 503
        
        # Define some interesting areas in Antwerp
        recommendations = [
            {
                'title': 'Central Station Area',
                'address': 'Koningin Astridplein 27, 2018 Antwerpen',
                'lat': 51.2175,
                'lon': 4.4214,
                'description': 'Excellent transport hub with direct connections to the central station, tram lines, and bus routes. Perfect for commuters.',
                'score': 9.2
            },
            {
                'title': 'Groenplaats',
                'address': 'Groenplaats, 2000 Antwerpen',
                'lat': 51.2197,
                'lon': 4.4034,
                'description': 'Historic square with great tram connections and shopping areas. Well-connected to the city center.',
                'score': 8.5
            },
            {
                'title': 'Eilandje District',
                'address': 'Sint-Laureiskaai, 2000 Antwerpen',
                'lat': 51.2289,
                'lon': 4.4089,
                'description': 'Modern waterfront area with good bus connections and velo stations. Popular for its museums and restaurants.',
                'score': 7.8
            },
            {
                'title': 'Zuid District',
                'address': 'De Keyserlei, 2018 Antwerpen',
                'lat': 51.2147,
                'lon': 4.4189,
                'description': 'Business district with excellent tram and bus connections. Close to the central station.',
                'score': 8.9
            },
            {
                'title': 'Het Zuid',
                'address': 'Leopold De Waelplaats, 2000 Antwerpen',
                'lat': 51.2075,
                'lon': 4.3975,
                'description': 'Cultural district with good public transport options and velo stations. Home to the Museum of Fine Arts.',
                'score': 7.5
            }
        ]
        
        # Calculate actual scores and enrich descriptions
        for rec in recommendations:
            score, details = calculate_accessibility_score(osm_data, rec['lat'], rec['lon'], 1.0)
            rec['score'] = score
            rec['description'] = generate_location_description(rec['lat'], rec['lon'], details)
        
        return jsonify({'recommendations': recommendations})
        
    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/isochrone')
def get_isochrone():
    """API endpoint to get areas reachable within a time limit (isochrone)"""
    try:
        # Get and validate parameters
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        time = request.args.get('time', '15')  # Time in minutes, default 15 min
        
        logger.debug(f"Received isochrone request with lat={lat}, lon={lon}, time={time}")
        
        # Convert parameters to float
        try:
            lat = float(lat)
            lon = float(lon)
            time = int(time)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter values: {e}")
            return jsonify({'error': 'Invalid parameter values'}), 400
        
        # Simple circle-based isochrone (no need for complex calculations for now)
        # Average speeds in Antwerp (km/h): Tram = 20, Bus = 15, Bike = 12, Walk = 5
        # We'll use a simplified approach with the highest speed (20 km/h for tram)
        max_speed_kmh = 20.0
        radius_km = (max_speed_kmh * time / 60.0)  # Convert minutes to hours
        
        # Create a simple circular polygon as GeoJSON
        num_points = 64
        coordinates = []
        
        for i in range(num_points):
            angle = (i / num_points) * (2 * math.pi)
            dx = radius_km * math.cos(angle)
            dy = radius_km * math.sin(angle)
            
            # Convert km to approximate degrees
            # 111.32 km = 1 degree of latitude
            # 111.32 * cos(lat) km = 1 degree of longitude at latitude 'lat'
            delta_lat = dy / 111.32
            delta_lon = dx / (111.32 * math.cos(math.radians(lat)))
            
            coordinates.append([lon + delta_lon, lat + delta_lat])
        
        # Close the polygon
        coordinates.append(coordinates[0])
        
        # Create GeoJSON feature
        isochrone = {
            "type": "Feature",
            "properties": {
                "time_minutes": time,
                "radius_km": radius_km,
                "transport_mode": "fastest_available"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            }
        }
        
        return jsonify({'isochrone': isochrone})
        
    except Exception as e:
        logger.error(f"Error in get_isochrone: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Load data at startup
    if not load_data():
        logger.warning("Failed to load initial data")
    app.run(host='0.0.0.0', port=5000, debug=True) 