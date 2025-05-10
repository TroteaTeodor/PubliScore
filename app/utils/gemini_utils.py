import requests
import logging
from typing import Optional
import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = os.getenv('GEMINI_API_URL')

if not GEMINI_API_KEY or not GEMINI_API_URL:
    raise ValueError("Missing required environment variables. Please check your .env file.")

location_cache = {}

def get_cache_key(lat: float, lon: float, transport_details: dict) -> str:
    """Generate a cache key for a location based on its coordinates and transport details."""
    return f"{lat:.4f}_{lon:.4f}_{transport_details.get('bus_stops', 0)}_{transport_details.get('tram_stops', 0)}_{transport_details.get('velo_stations', 0)}"

def generate_location_description(lat: float, lon: float, transport_details: dict) -> Optional[str]:
    """
    Generate a description of a location using the Gemini API based on its coordinates and transport details.
    Uses caching to avoid unnecessary API calls for the same location.
    
    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        transport_details (dict): Dictionary containing transport information
        
    Returns:
        Optional[str]: Generated description or None if the API call fails
    """
    try:
        cache_key = get_cache_key(lat, lon, transport_details)
        
        if cache_key in location_cache:
            logger.debug("Using cached description for location")
            return location_cache[cache_key]
        
        prompt = f"""Generate a short, friendly description of this location in Antwerp based on its public transport accessibility:
        - Bus stops: {transport_details.get('bus_stops', 0)}
        - Tram stops: {transport_details.get('tram_stops', 0)}
        - Velo stations: {transport_details.get('velo_stations', 0)}
        - Closest bus stop: {transport_details.get('closest_bus', 'N/A')} km
        - Closest tram stop: {transport_details.get('closest_tram', 'N/A')} km
        - Closest velo station: {transport_details.get('closest_velo', 'N/A')} km
        
        Keep the description concise (2-3 sentences) and focus on the transport accessibility."""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 200,
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Making Gemini API request to {GEMINI_API_URL}")
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.debug(f"Gemini API response: {result}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                if 'content' in result['candidates'][0] and 'parts' in result['candidates'][0]['content']:
                    description = result['candidates'][0]['content']['parts'][0]['text']
                    location_cache[cache_key] = description
                    return description
            
            logger.error("No content generated in Gemini API response")
            return None
        else:
            error_msg = f"Gemini API request failed with status code: {response.status_code}"
            try:
                error_details = response.json()
                error_msg += f"\nError details: {error_details}"
            except:
                error_msg += f"\nResponse content: {response.text}"
            logger.error(error_msg)
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Gemini API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during Gemini API request: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating location description: {e}")
        return None 