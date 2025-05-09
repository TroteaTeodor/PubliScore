# PubliScore

PubliScore is a web application that calculates public transport accessibility scores for locations in Antwerp. It helps students and eco-conscious residents find accommodations with good public transport connections.

## Features

- Search for any location in Antwerp by address or by clicking on a map
- Get an accessibility score from 0-10 based on public transport availability
- View details about nearby public transport stops
- Interactive map for exploration

## How It Works

PubliScore uses OpenStreetMap data for Antwerp to calculate accessibility scores. The scoring algorithm considers:
- Number of public transport stops within 1km
- Distance to the nearest stop
- Types of transport available

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PubliScore.git
cd PubliScore
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and go to `http://localhost:5000`

## Dataset

The application uses the [Antwerp OSM Navigator dataset](https://huggingface.co/datasets/ns2agi/antwerp-osm-navigator) from Hugging Face, which contains OpenStreetMap data for the city of Antwerp.

## Project Structure

```
PubliScore/
│
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
│
├── app/
│   ├── static/               # Static assets (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── search.html
│   │   └── team.html
│   │
│   ├── models/               # Scoring models and algorithms
│   │   └── scoring.py
│   │
│   └── utils/                # Utility functions
│       └── data_loader.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 