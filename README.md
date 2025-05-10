# PubliScore: Antwerp Public Transport Accessibility Scoring System

## Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Technologies and Dependencies](#technologies-and-dependencies)
- [Core Components](#core-components)
- [Accessibility Scoring Algorithm](#accessibility-scoring-algorithm)
- [Data Processing Pipeline](#data-processing-pipeline)
- [API Documentation](#api-documentation)
- [Interactive Map Functionality](#interactive-map-functionality)
- [Heatmap Visualization](#heatmap-visualization)
- [Location Recommendations](#location-recommendations)
- [Installation and Setup](#installation-and-setup)
- [Development Guidelines](#development-guidelines)
- [Known Limitations and Future Improvements](#known-limitations-and-future-improvements)
- [Credits and Acknowledgments](#credits-and-acknowledgments)

## Project Overview

PubliScore is an advanced geospatial analysis application that evaluates and visualizes public transport accessibility across the Antwerp metropolitan area. The system processes OpenStreetMap (OSM) data to calculate accessibility scores based on proximity to various transport options including bus stops, tram stations, and Velo bike-sharing locations.

The project aims to help residents, urban planners, real estate developers, and public transportation authorities make informed decisions by providing objective measurements of transport accessibility. Users can search specific addresses, visualize transport density through heatmaps, and receive location recommendations based on accessibility scores.

## Architecture

PubliScore follows a modern web application architecture with distinct frontend and backend components:

### Backend Architecture
- **Framework**: Flask-based Python backend serving as both API and web server
- **Data Management**: In-memory caching of OSM data using Python's LRU cache decorator
- **External Data Sources**: HuggingFace datasets for OSM data retrieval
- **API Layer**: RESTful JSON endpoints for accessibility scoring, location recommendations, and transport node information

### Frontend Architecture
- **Templating**: Jinja2 templates extending from a base layout
- **Mapping**: Leaflet.js for interactive mapping and visualization
- **UI Components**: Bootstrap 5 with custom CSS for responsive design
- **Data Visualization**: Leaflet Heat plugin for transport density heatmaps
- **Dynamic Content**: Vanilla JavaScript for DOM manipulation and API interactions

### Data Flow
1. OSM data is loaded during application startup and cached in memory
2. User queries (address searches or map clicks) trigger API requests
3. Backend processes geospatial calculations and returns structured data
4. Frontend renders visualizations, scores, and recommendations based on returned data

## Technologies and Dependencies

### Backend
- **Python 3.9+**: Core programming language
- **Flask**: Web framework
- **Pandas**: Data processing and analysis
- **NumPy**: Numerical computations
- **Geopy**: Geographical distance calculations
- **Datasets (HuggingFace)**: Accessing and loading OSM data
- **JSON**: Data serialization

### Frontend
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Bootstrap 5**: UI framework
- **Leaflet.js**: Interactive mapping
- **Leaflet.heat**: Heatmap visualization
- **Nominatim API**: Geocoding for address searches

## Core Components

### Data Loader
Located in `app/utils/data_loader.py`, this component:
- Retrieves Antwerp OSM data from HuggingFace dataset "ns2agi/antwerp-osm-navigator"
- Filters for transport-related nodes (bus stops, tram stops, Velo stations)
- Implements caching mechanisms to optimize memory usage
- Provides a clean, normalized dataset for scoring calculations

### Scoring Engine
Located in `app/models/scoring.py`, this component:
- Calculates accessibility scores based on multiple weighted factors
- Implements geographical distance calculations
- Provides detailed breakdown of transport options
- Supports variable radius parameters for different analysis scenarios

### Gemini Integration
Located in `app/utils/gemini_utils.py`, this component:
- Generates natural language descriptions of locations
- Enhances user experience with contextual information
- Leverages Google's Gemini API for intelligent content generation

### Web Interface
Spread across multiple templates in `app/templates/`, this component:
- Provides intuitive map-based interface for exploring accessibility
- Displays detailed transport information and scoring
- Enables address search and location selection
- Visualizes transport density through customizable heatmaps
- Presents curated location recommendations

## Accessibility Scoring Algorithm

The core scoring algorithm employs a sophisticated multi-factor approach to quantify transport accessibility:

1. **Proximity Weighting**: Transport nodes closer to the target location receive higher weights
2. **Transport Type Importance**: Different transport types have varying weights:
   - Tram stops: 1.2x weight (most valuable due to speed and capacity)
   - Bus stops: 0.8x weight (standard baseline)
   - Velo stations: 0.6x weight (supplementary transport)
3. **Density Consideration**: Areas with multiple transport options score higher
4. **Coverage Analysis**: Transport options are evaluated within the specified radius
5. **Normalized Output**: Final scores are normalized to a 0-10 scale for intuitive understanding

### Scoring Formula
The scoring formula can be represented as:

```
Score = Σ(Wi × Di × Ti) / Nmax × 10
```
Where:
- Wi = Weight based on distance to transport node i
- Di = Decay factor based on distance (closer nodes count more)
- Ti = Transport type modifier for node i
- Nmax = Normalization factor to ensure 0-10 scale

## Data Processing Pipeline

### Initial Data Acquisition
1. OSM data for Antwerp is accessed via HuggingFace datasets
2. Data is filtered for transport-related nodes
3. Coordinates and transport types are normalized and validated

### Runtime Processing
1. User selects location (via map click or address search)
2. Location coordinates and search radius are passed to scoring API
3. Spatial filtering identifies transport nodes within radius
4. Distance calculations determine proximity factors
5. Scoring algorithm applies weights and normalizations
6. Detailed results are returned as structured JSON

### Heatmap Generation
1. All transport nodes are retrieved from the backend
2. Each node is assigned intensity based on transport type
3. User-adjustable intensity factor modifies visualization
4. Leaflet.heat plugin renders the density visualization

## API Documentation

PubliScore exposes several RESTful endpoints:

### GET /api/score
Returns accessibility score and transport details for a location.

**Parameters:**
- `lat` (float): Latitude of target location
- `lon` (float): Longitude of target location
- `radius` (float): Search radius in kilometers (default: 1.0)

**Response:**
```json
{
  "score": 7.5,
  "details": {
    "bus_stops": 5,
    "tram_stops": 2,
    "velo_stations": 3,
    "closest_bus": 0.25,
    "closest_tram": 0.48,
    "closest_velo": 0.33
  },
  "transport_nodes": [...],
  "location_description": "This area has excellent public transport accessibility..."
}
```

### GET /api/all_transport_nodes
Returns all transport nodes for heatmap visualization.

**Parameters:** None

**Response:**
```json
{
  "transport_nodes": [
    {
      "lat": 51.2195,
      "lon": 4.4025,
      "transport_type": "bus_stop"
    },
    ...
  ]
}
```

### GET /api/recommendations
Returns recommended locations with accessibility scores.

**Parameters:** None

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Central Station Area",
      "address": "Koningin Astridplein 27, 2018 Antwerpen",
      "lat": 51.2175,
      "lon": 4.4214,
      "description": "Excellent transport hub with direct connections...",
      "score": 9.2
    },
    ...
  ]
}
```

## Interactive Map Functionality

The map interface (`app/templates/search.html`) provides several interactive features:

### Location Selection
- Users can click directly on the map to select a location
- Address search utilizes Nominatim API for geocoding
- Selected locations display a marker with adjustable radius circle

### Transport Visualization
- Transport nodes are displayed with color-coding:
  - Blue markers: Bus stops
  - Purple markers: Tram stops
  - Orange markers: Velo stations
- Popup information displays transport type and distance

### Dynamic Radius Adjustment
- Slider control adjusts search radius from 0.5km to 3.0km
- Direct input field allows precise radius specification
- Radius changes trigger automatic recalculation of scores

## Heatmap Visualization

The heatmap functionality provides density visualization for transport nodes:

### Features
- Toggle control to show/hide heatmap
- Intensity slider to adjust visualization density
- Color gradient from blue (low) to red (high) density
- Weighted visualization based on transport types

### Technical Implementation
- Leaflet.heat plugin for rendering
- Custom intensity calculation based on transport type
- Dynamic radius and blur adjustments based on zoom level
- Efficient data processing for smooth performance

## Location Recommendations

The recommendation system provides curated location suggestions:

### Implementation
- Five diverse locations across Antwerp
- Real-time accessibility score calculation
- Dynamic description generation using location context
- Interactive cards with location preview functionality

### Recommendation Selection Logic
- Geographic diversity across Antwerp districts
- Variety of transport accessibility profiles
- Mix of urban center and peripheral locations
- Historical and cultural significance consideration

## Installation and Setup

### Prerequisites
- Python 3.9+
- pip package manager
- Git

### Installation Steps
1. Clone the repository:
   ```
   git clone https://github.com/your-username/PubliScore.git
cd PubliScore
```

2. Create and activate virtual environment:
   ```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
   ```
pip install -r requirements.txt
```

4. Run the application:
   ```
python app.py
```

5. Access the application:
   Open http://localhost:5000 in your web browser

## Development Guidelines

### Project Structure
```
PubliScore/
├── app.py                  # Application entry point
├── app/
│   ├── templates/          # Jinja2 templates
│   │   ├── base.html       # Base template
│   │   ├── home.html       # Home page
│   │   ├── search.html     # Main search interface
│   │   └── team.html       # Team information
│   ├── static/             # Static assets
│   ├── models/             # Data models and calculations
│   │   └── scoring.py      # Accessibility scoring logic
│   └── utils/              # Utility functions
│       ├── data_loader.py  # OSM data loading
│       └── gemini_utils.py # Gemini API integration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

### Coding Standards
- Follow PEP 8 guidelines for Python code
- Use JSDoc comments for JavaScript functions
- Maintain consistent indentation (4 spaces for Python, 2 spaces for JS/HTML)
- Include docstrings for all functions and classes
- Write clear, descriptive variable and function names

## Known Limitations and Future Improvements

### Current Limitations
- OSM data may not include all transport options
- Scoring algorithm does not account for service frequency
- Limited to Antwerp metropolitan area
- No user accounts or saved preferences
- Static recommendations without personalization

### Planned Enhancements
- Incorporate GTFS data for schedule-aware accessibility scoring
- Extend coverage to additional Belgian cities
- Implement user accounts with saved locations
- Develop personalized recommendations based on user preferences
- Add time-based accessibility analysis (different times of day)
- Integrate comparative analysis between locations
- Develop mobile applications for iOS and Android

## Credits and Acknowledgments

- **OpenStreetMap**: Primary data source for transport node information
- **HuggingFace**: Dataset hosting and distribution
- **Google Gemini API**: Natural language generation
- **Leaflet.js**: Interactive mapping framework
- **Bootstrap**: UI framework
- **Flask**: Web framework

---

Development team:
- Teodor Trotea - Backend Development
- Alexander Sorodoc - Frontend Implementation
- Eugen Donescu - Data Processing

This project was developed during the Agentic Hackathon I (March 2025) organized by North Star AGI, an organization dedicated to building the future of autonomous AI agents.

© 2025 PubliScore Team. All rights reserved. 