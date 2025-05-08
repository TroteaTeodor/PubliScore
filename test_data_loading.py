"""
Test script to verify the OSM data loading functionality
"""
from utils.data_loader import load_osm_data

def test_data_loading():
    """
    Test that we can load and process the OSM data correctly
    """
    print("Testing data loading...")
    
    # Load the data
    osm_data = load_osm_data()
    
    # Print some basic statistics
    print(f"\nTotal transport nodes loaded: {len(osm_data)}")
    
    # Count by transport type
    transport_types = osm_data['transport_type'].value_counts()
    print("\nTransport types distribution:")
    for transport_type, count in transport_types.items():
        print(f"- {transport_type}: {count}")
    
    # Check for a sample location in central Antwerp
    lat, lon = 51.2194, 4.4025  # Central Station area
    print(f"\nTesting proximity calculation for location: {lat}, {lon}")
    
    # Import the grading module to test proximity
    from utils.grading import find_nearby_transport
    
    # Find nearby transport
    nearby = find_nearby_transport(osm_data, lat, lon, max_distance=0.5)
    
    print(f"Found {len(nearby)} transport options within 0.5 km")
    
    if not nearby.empty:
        print("\nClosest 5 transport options:")
        for _, row in nearby.head(5).iterrows():
            print(f"- {row['type']} at {row['distance_km']:.3f} km")
    
    print("\nData loading test complete!")
    return osm_data

if __name__ == "__main__":
    test_data_loading() 