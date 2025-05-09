# PubliScore

PubliScore is a web application that helps users evaluate the public transport accessibility of locations in Antwerp, Belgium. It provides a score from 0-10 based on the proximity and availability of bus stops, tram stops, and Velo (bike sharing) stations.

## Features

- Interactive map interface for location selection
- Real-time accessibility scoring
- Detailed breakdown of nearby transport options
- Support for different search radii (500m to 3km)
- Visual representation of transport nodes on the map
- Responsive design for both desktop and mobile devices

## Scoring System

The accessibility score (0-10) is calculated based on:

- **Bus Stops** (max 3 points)
  - 0.4 points per stop up to 7-8 stops
  - Distance-based decay using exponential function

- **Tram Stops** (max 4 points)
  - 1.0 point per stop up to 4 stops
  - Distance-based decay using exponential function

- **Velo Stations** (max 3 points)
  - 0.6 points per station up to 5 stations
  - Distance-based decay using exponential function

## Score Interpretation

- 8-10: Excellent public transport accessibility
- 6-7.9: Good public transport accessibility
- 4-5.9: Moderate public transport accessibility
- 2-3.9: Limited public transport accessibility
- 0-1.9: Poor public transport accessibility
- 0: No public transport available in the area

## Technical Details

### Data Source
- Uses OpenStreetMap data for Antwerp
- Data includes bus stops, tram stops, and Velo stations
- Data is loaded from HuggingFace dataset "ns2agi/antwerp-osm-navigator"

### Technologies Used
- Backend: Python/Flask
- Frontend: HTML, CSS, JavaScript
- Mapping: Leaflet.js
- Data Processing: Pandas, NumPy
- Geocoding: Nominatim

### Distance Calculation
- Uses Haversine formula for accurate distance calculations
- Considers Earth's curvature for precise measurements
- Distances are calculated in kilometers

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PubliScore.git
cd PubliScore
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Open the application in your web browser
2. Enter an address in Antwerp or click on the map to select a location
3. Choose your desired search radius (500m to 3km)
4. View the accessibility score and nearby transport options
5. Explore the map to see the exact locations of transport nodes

## Limitations

- Currently only supports Antwerp, Belgium
- Requires internet connection for map tiles and geocoding
- Search radius limited to 3km maximum
- Score is based on proximity only, not on service frequency or quality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenStreetMap for the base map data
- HuggingFace for hosting the Antwerp OSM dataset
- Leaflet.js for the interactive mapping functionality
- Nominatim for geocoding services 