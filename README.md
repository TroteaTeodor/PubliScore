# AreaGrade

AreaGrade helps you find the best areas to rent in Antwerp based on public transport accessibility. The project analyzes OpenStreetMap data to evaluate areas based on their proximity to tram stops, bus stops, and Velo bike sharing stations.

## Features

- Interactive map showing transportation options
- Detailed scoring for bus, tram, and Velo access
- AI-powered insights on area accessibility
- Mobile-friendly design for on-the-go searches

## Setup

1. Clone the repository:
```bash
git clone https://github.com/TroteaTeodor/AreaGrade.git
cd AreaGrade
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

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your Google API key for Gemini AI in the `.env` file

5. Run the application:
```bash
python app.py
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

- `GOOGLE_API_KEY`: Your Google API key for Gemini AI (get it from [Google AI Studio](https://aistudio.google.com/apikey))

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenStreetMap for the transportation data
- Google's Gemini AI for providing insights
- The Hugging Face community for the Antwerp OSM Navigator dataset







