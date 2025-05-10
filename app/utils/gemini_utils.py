import requests
import logging
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = os.getenv('GEMINI_API_URL')

if not GEMINI_API_KEY or not GEMINI_API_URL:
    raise ValueError("Missing required environment variables. Please check your .env file.")

def generate_location_description(lat: float, lon: float, transport_details: dict) -> Optional[str]:
    """
    Generate a description of a location using the Gemini API based on its coordinates and transport details.
    
    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        transport_details (dict): Dictionary containing transport information
        
    Returns:
        Optional[str]: Generated description or None if the API call fails
    """
    try:
        # Construct the prompt
        prompt = f"""Generate a short, friendly description of this location in Antwerp based on its public transport accessibility:
        - Bus stops: {transport_details.get('bus_stops', 0)}
        - Tram stops: {transport_details.get('tram_stops', 0)}
        - Velo stations: {transport_details.get('velo_stations', 0)}
        - Closest bus stop: {transport_details.get('closest_bus', 'N/A')} km
        - Closest tram stop: {transport_details.get('closest_tram', 'N/A')} km
        - Closest velo station: {transport_details.get('closest_velo', 'N/A')} km
        
        Keep the description concise (2-3 sentences) and focus on the transport accessibility."""

        # Prepare the request payload
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        # Make the API request
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"Gemini API response: {result}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content']:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            logger.error("No content generated in Gemini API response")
            return None
        else:
            logger.error(f"Gemini API request failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating location description: {e}")
        return None 