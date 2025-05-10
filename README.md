# PubliScore

A web application for evaluating public transport accessibility in Antwerp.

## Features

- Interactive map visualization
- Location-based accessibility scoring
- Transport node analysis (bus stops, tram stops, velo stations)
- Travel time analysis with isochrone visualization
- AI-powered location recommendations
- Transport density heatmap

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PubliScore.git
cd PubliScore
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
```

## Usage

### Starting the Application

1. Activate virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run Flask:
```bash
flask run
```

3. Open in browser:
```
http://localhost:5000
```

### Using the Application

1. **Search Locations**
   - Enter address or click on map
   - Adjust search radius with slider

2. **View Scores**
   - Check accessibility score
   - View transport details
   - Read location description

3. **Travel Time Analysis**
   - Toggle "Show reachable areas"
   - Adjust time limit
   - View coverage areas

4. **Transport Options**
   - Toggle heatmap
   - Click nodes for details
   - View recommendations

## Project Structure

```
PubliScore/
├── app/
│   ├── models/
│   │   ├── scoring.py
│   │   └── transport_node.py
│   ├── templates/
│   │   ├── base.html
│   │   └── search.html
│   ├── utils/
│   │   ├── gtfs_loader.py
│   │   └── scoring_utils.py
│   └── __init__.py
├── data/
│   └── transport_nodes.csv
├── app.py
├── requirements.txt
└── README.md
```

## Dependencies

- Flask
- Leaflet
- Pandas
- NumPy
- Shapely

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License

## Acknowledgments

- OpenStreetMap
- De Lijn
- Antwerp City 