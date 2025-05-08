from flask import Flask, render_template, request, jsonify
import folium
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import pandas as pd
from pathlib import Path
import requests
import jinja2

# Import our custom modules
from utils.data_loader import load_osm_data
from utils.grading import calculate_area_grade, haversine

# Load environment variables
load_dotenv()

# Set up directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Configure Gemini API - with proper error handling
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
gemini_model = None

try:
    if GOOGLE_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        print("Gemini API configured successfully")
except ImportError:
    print("Google Generative AI module not installed. AI features will be disabled.")
except Exception as e:
    print(f"Error configuring Gemini API: {str(e)}")

# Initialize Flask app
app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)

# Global variable to store OSM data
osm_data = None

# Define custom filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags"""
    if not value:
        return ""
    return jinja2.Markup(value.replace('\n', '<br>'))

def geocode_address(address):
    """
    Geocode an address to get its coordinates.
    
    Args:
        address (str): The address to geocode
        
    Returns:
        dict: Dictionary containing lat and lon, or None if geocoding failed
    """
    try:
        # Initialize geocoder with a more specific user agent
        geolocator = Nominatim(
            user_agent="AreaGrade/1.0 (https://github.com/yourusername/AreaGrade; your@email.com)",
            timeout=10
        )
        
        # Try different variations of the address
        variations = [
            f"{address}, Antwerp, Belgium",
            f"{address}, Antwerpen, Belgium",
            address  # Try the original address as a fallback
        ]
        
        for addr in variations:
            try:
                location = geolocator.geocode(addr)
                if location is not None:
                    # Verify the location is in Antwerp
                    if "antwerp" in location.address.lower() or "antwerpen" in location.address.lower():
                        return {
                            'lat': location.latitude,
                            'lon': location.longitude
                        }
            except Exception as e:
                print(f"Geocoding attempt failed for {addr}: {str(e)}")
                continue
        
        print(f"Could not geocode address: {address}")
        return None
            
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return None

@app.route('/')
def index():
    """Home page with the search form"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Process the search request and calculate area grade"""
    global osm_data
    
    if osm_data is None:
        print("Loading OSM data...")
        osm_data = load_osm_data()
        print("Data loaded successfully!")
    
    try:
        # Check if we're using geolocation
        use_geolocation = request.form.get('useGeolocation') == 'true'
        
        if use_geolocation:
            # Get coordinates from form
            try:
                latitude = float(request.form.get('latitude'))
                longitude = float(request.form.get('longitude'))
                address = get_address_from_coords(latitude, longitude)
            except (ValueError, TypeError) as e:
                return jsonify({"error": f"Invalid coordinates: {str(e)}"}), 400
        else:
            # Get address from form
            address = request.form.get('address')
            if not address:
                return jsonify({"error": "No address provided"}), 400
                
            # Geocode the address
            geocoded = geocode_address(address)
            if not geocoded:
                return jsonify({"error": "Could not geocode address"}), 400
                
            latitude = geocoded['lat']
            longitude = geocoded['lon']
        
        # Define types to exclude
        exclude_types = ['unknown', 'platform']
        
        # Calculate grade using cached data
        grade_results = calculate_area_grade(osm_data, latitude, longitude)
        
        # Generate AI explanation for the grade if Gemini API is configured
        ai_explanation = None
        if GOOGLE_API_KEY:
            try:
                # Create prompt for AI explanation
                nearby_transport_text = ""
                for transport in grade_results.get('nearby_transport', [])[:5]:
                    nearby_transport_text += f"- {transport['type'].capitalize()}: {transport['name']} ({transport['distance_km']} km away)\n"
                
                prompt = f"""
                The area at {address} has received the following scores for public transportation:
                - Overall grade: {grade_results['overall_grade']} ({grade_results['overall_score']} / 100)
                - Bus score: {grade_results['bus_score']} / 100
                - Tram score: {grade_results['tram_score']} / 100
                - Velo bike score: {grade_results['velobike_score']} / 100
                
                Nearby transport options include:
                {nearby_transport_text}
                
                Please give a brief (2-3 sentences) assessment of this area's public transport accessibility.
                Is it good for professionals, students, or families?
                Be specific about what makes it a {grade_results['overall_grade']} area.
                """
                
                response = gemini_model.generate_content(prompt)
                ai_explanation = response.text
            except Exception as e:
                print(f"Gemini API error: {str(e)}")
                ai_explanation = None
        
        # Create map centered on the address
        map_obj = folium.Map(
            location=[latitude, longitude],
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Add marker for the address
        folium.Marker(
            location=[latitude, longitude],
            popup=f"<b>Selected Location</b><br>{address}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(map_obj)
        
        # Get bus routes near the location
        bus_routes = osm_data[
            (osm_data['transport_type'] == 'bus_route') & 
            (osm_data['route_ref'].notna())
        ]
        
        # Add bus routes to map
        for _, route in bus_routes.iterrows():
            # Get route path from OSM data
            route_path = get_route_path(osm_data, route['route_ref'])
            if route_path:
                # Create polyline for the route
                folium.PolyLine(
                    locations=route_path,
                    popup=f"Bus {route['route_ref']}",
                    color='blue',
                    weight=2,
                    opacity=0.7
                ).add_to(map_obj)
        
        # Add markers for nearby transport options
        for transport in grade_results.get('nearby_transport', []):
            # Skip unnamed transport points
            if not transport.get('name') or str(transport.get('name')).strip() == '':
                continue
                
            # Skip unwanted types
            if transport['type'] in exclude_types or transport['type'] == 'stop_position':
                continue
                
            # Choose icon based on transport type
            icon_color = 'blue'
            icon_name = 'info-sign'
            
            if transport['type'] == 'bus' or transport['type'] == 'bus_stop':
                icon_name = 'bus'
            elif transport['type'] == 'tram' or transport['type'] == 'tram_stop':
                icon_color = 'green'
                icon_name = 'subway'
            elif transport['type'] == 'velobike':
                icon_color = 'purple'
                icon_name = 'bicycle'
                
            # Get bus routes serving this stop
            serving_routes = get_serving_routes(osm_data, transport['lat'], transport['lon'])
            route_info = ""
            if serving_routes:
                route_info = f"<br>Serves: {', '.join(serving_routes)}"
                
            folium.Marker(
                location=[transport['lat'], transport['lon']],
                popup=f"<b>{transport['type'].capitalize()}</b><br>{transport.get('name', 'No name')}<br>{transport['distance_km']} km{route_info}",
                icon=folium.Icon(color=icon_color, icon=icon_name)
            ).add_to(map_obj)
        
        # Save map to static directory instead of templates
        map_path = os.path.join(app.static_folder, 'temp_map.html')
        map_obj.save(map_path)
        
        return render_template(
            'results.html', 
            address=address,
            latitude=latitude,
            longitude=longitude,
            grade_results=grade_results,
            ai_explanation=ai_explanation
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_route_path(osm_data, route_ref):
    """Get the path coordinates for a bus route"""
    # Find all nodes that are part of this route
    route_nodes = osm_data[
        (osm_data['route_ref'] == route_ref) & 
        (osm_data['transport_type'].isin(['bus', 'bus_stop', 'bus_route']))
    ]
    
    if route_nodes.empty:
        return None
        
    # Sort nodes by their position in the route
    route_nodes = route_nodes.sort_values('id')
    
    # Extract coordinates
    path = list(zip(route_nodes['lat'], route_nodes['lon']))
    return path

def get_serving_routes(osm_data, lat, lon, max_distance=0.1):
    """Get bus routes that serve a particular stop"""
    # Find bus routes near the stop
    nearby_routes = osm_data[
        (osm_data['transport_type'] == 'bus_route') &
        (osm_data['route_ref'].notna())
    ]
    
    serving_routes = set()
    for _, route in nearby_routes.iterrows():
        # Check if this route has a stop near the given coordinates
        route_stops = osm_data[
            (osm_data['route_ref'] == route['route_ref']) &
            (osm_data['transport_type'].isin(['bus', 'bus_stop']))
        ]
        
        for _, stop in route_stops.iterrows():
            distance = haversine(lon, lat, stop['lon'], stop['lat'])
            if distance <= max_distance:
                serving_routes.add(route['route_ref'])
                break
                
    return sorted(list(serving_routes))

def get_address_from_coords(lat, lon):
    """Get address from coordinates using Nominatim reverse geocoding"""
    try:
        geolocator = Nominatim(user_agent="AreaGrade")
        location = geolocator.reverse(f"{lat}, {lon}")
        
        if location and location.address:
            return location.address
        else:
            return f"Location at {lat:.5f}, {lon:.5f}"
    except Exception:
        return f"Location at {lat:.5f}, {lon:.5f}"

@app.route('/about')
def about():
    """About page with information about the project and AI insights"""
    ai_insights = ""
    if GOOGLE_API_KEY:
        try:
            prompt = "Give me 3 benefits of living near good public transportation in a city like Antwerp. Be brief, concise, and provide a numbered list."
            response = gemini_model.generate_content(prompt)
            ai_insights = response.text
        except Exception as e:
            print(f"Gemini API error in about page: {str(e)}")
            ai_insights = "1. Easy access to the city center and major attractions without needing a car.\n\n2. Lower transportation costs and reduced need for car ownership.\n\n3. Better environmental impact with reduced carbon emissions from using public transit instead of personal vehicles."
    else:
        ai_insights = "1. Easy access to the city center and major attractions without needing a car.\n\n2. Lower transportation costs and reduced need for car ownership.\n\n3. Better environmental impact with reduced carbon emissions from using public transit instead of personal vehicles."

    return render_template('about.html', ai_insights=ai_insights)

@app.route('/team')
def team():
    """Team page showing project contributors"""
    team_members = [
        {
            'name': 'Teodor Trotea',
            'role': 'Team Lead & Backend Developer',
            'bio': 'Passionate about geospatial data analysis and transportation systems.',
            'image': 'https://api.dicebear.com/7.x/avataaars/svg?seed=teodor'
        },
        {
            'name': 'Alexis de Maleprade',
            'role': 'Front-end Developer',
            'bio': 'Experienced in creating intuitive user interfaces and interactive maps.',
            'image': 'https://api.dicebear.com/7.x/avataaars/svg?seed=alexis'
        },
        {
            'name': 'Maya Johnson',
            'role': 'Data Scientist',
            'bio': 'Specializes in machine learning models for urban transportation analysis.',
            'image': 'https://api.dicebear.com/7.x/avataaars/svg?seed=maya'
        },
        {
            'name': 'Carlos Rodriguez',
            'role': 'GIS Specialist',
            'bio': 'Expert in OpenStreetMap data processing and geospatial visualization.',
            'image': 'https://api.dicebear.com/7.x/avataaars/svg?seed=carlos'
        }
    ]
    return render_template('team.html', team_members=team_members)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    print(f"Server error: {str(e)}")
    return render_template('500.html'), 500

def main():
    """Initialize and run the Flask app"""
    global osm_data
    
    # Create necessary directories
    os.makedirs(os.path.join(BASE_DIR, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'static/css'), exist_ok=True)
    
    # Load data when app starts
    print("Loading OSM data...")
    osm_data = load_osm_data()
    print("Data loaded successfully!")
    
    # Run the app
    app.run(debug=True)

if __name__ == '__main__':
    main() 