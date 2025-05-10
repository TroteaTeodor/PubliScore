from flask import request, jsonify

@app.route('/api/location_info')
def get_location_info():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    try:
        # Fetch De Lijn data
        delijn_data = fetch_delijn_data(lat, lon)
        
        # Fetch neighborhood data
        neighborhood_data = fetch_neighborhood_data(lat, lon)
        
        # Combine all data
        location_data = {
            'delijn_frequency': delijn_data.get('frequency', 'unknown'),
            'delijn_reliability': delijn_data.get('reliability', 0.5),
            'delijn_coverage': delijn_data.get('coverage', 'unknown'),
            'neighborhood_quality': neighborhood_data.get('quality', 'unknown'),
            'has_sidewalks': neighborhood_data.get('has_sidewalks', False),
            'has_bike_lanes': neighborhood_data.get('has_bike_lanes', False),
            'has_crosswalks': neighborhood_data.get('has_crosswalks', False),
            'safety_rating': neighborhood_data.get('safety_rating', 5)
        }
        
        return jsonify(location_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def fetch_delijn_data(lat, lon):
    # TODO: Implement actual De Lijn API integration
    # For now, return mock data
    return {
        'frequency': 'medium',
        'reliability': 0.75,
        'coverage': 'fair'
    }

def fetch_neighborhood_data(lat, lon):
    # TODO: Implement actual neighborhood data fetching
    # For now, return mock data
    return {
        'quality': 'fair',
        'has_sidewalks': True,
        'has_bike_lanes': True,
        'has_crosswalks': True,
        'safety_rating': 6
    } 