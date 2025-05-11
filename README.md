# PubliScore

PubliScore is a web application that helps users evaluate the public transport accessibility of locations in Antwerp.

## Features

- Interactive map interface
- Real-time public transport accessibility scoring
- Location recommendations
- Transport node visualization
- Heatmap of transport density

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PubliScore.git
cd PubliScore
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Gemini API key:
```
GEMINI_API_KEY="your-api-key-here"
GEMINI_API_URL="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

### Deploying to Render

1. Create a Render account at https://render.com

2. Create a new Web Service:
   - Connect your GitHub repository
   - Select "Python" as the runtime
   - Render will automatically detect the `render.yaml` configuration

3. Add your environment variables in the Render dashboard:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GEMINI_API_URL`: The Gemini API URL

4. Deploy!

Your application will be available at `https://publiscore.onrender.com` (or a similar URL)

### Alternative Deployment Options

- **Heroku**: Use the Procfile for Heroku deployment
- **DigitalOcean**: Deploy to a DigitalOcean App Platform
- **AWS**: Deploy to AWS Elastic Beanstalk
- **Google Cloud**: Deploy to Google Cloud Run

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Overview

PubliScore analyzes the accessibility of locations in Antwerp by considering:
- Proximity to bus stops, tram stops, and velo stations
- Travel time analysis with isochrone visualization
- Transport density mapping
- AI-powered location recommendations

The system provides detailed scoring and insights to help residents, urban planners, and real estate developers understand the public transport accessibility of any location in Antwerp.

## Features

### Interactive Map Visualization
- Real-time location selection
- Dynamic radius adjustment
- Color-coded transport nodes
- Customizable search parameters

### Accessibility Scoring
- Comprehensive scoring system (0-10 scale)
- Weighted analysis of transport options
- Detailed breakdown of transport availability
- Location-specific descriptions

### Travel Time Analysis
- Isochrone visualization for different transport modes
- Adjustable time limits (5-60 minutes)
- Multiple transport mode coverage (tram, bus, bike, walk)
- Speed-based distance calculations

### Transport Analysis
- Bus stop proximity and density
- Tram stop accessibility
- Velo station availability
- Transport node clustering

### AI-Powered Features
- Location recommendations
- Area descriptions
- Transport accessibility insights
- Personalized suggestions

### Heatmap Visualization
- Transport density mapping
- Adjustable intensity levels
- Color-coded density representation
- Real-time updates

## Technical Details

### Backend Architecture
- Flask-based Python backend
- RESTful API endpoints
- Efficient data processing
- Caching mechanisms

### Frontend Implementation
- Interactive Leaflet.js maps
- Bootstrap 5 UI framework
- Responsive design
- Dynamic content updates

### Data Processing
- OSM data integration
- Transport node filtering
- Distance calculations
- Score normalization

## Project Structure

```
PubliScore/
├── app/
│   ├── models/
│   │   ├── scoring.py          # Accessibility scoring logic
│   │   └── transport_node.py   # Transport node data model
│   ├── templates/
│   │   ├── base.html          # Base template
│   │   └── search.html        # Main search interface
│   ├── utils/
│   │   ├── gtfs_loader.py     # GTFS data processing
│   │   └── scoring_utils.py   # Scoring calculations
│   └── __init__.py
├── data/
│   └── transport_nodes.csv    # Transport node data
├── app.py                     # Application entry point
├── requirements.txt           # Python dependencies
└── README.md
```

## Dependencies

### Backend
- Flask: Web framework
- Pandas: Data manipulation
- NumPy: Numerical computations
- Shapely: Geometric operations

### Frontend
- Leaflet.js: Interactive mapping
- Bootstrap 5: UI framework
- JavaScript: Dynamic content

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License

## Acknowledgments

- OpenStreetMap for map data
- De Lijn for public transport information
- Antwerp City for velo station data

## Development Team

- Teodor Trotea - Backend Development
- Alexander Sorodoc - Frontend Implementation
- Eugen Donescu - Data Processing

This project was developed during the Agentic Hackathon I (March 2025) organized by North Star AGI, an organization dedicated to building the future of autonomous AI agents.

© 2025 PubliScore Team. All rights reserved. 
