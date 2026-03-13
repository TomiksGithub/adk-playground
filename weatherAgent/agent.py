import requests
from pathlib import Path
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents import Agent


def get_weather(city: str) -> dict:
    """Get current weather for a given city using the Open-Meteo API.

    Args:
        city: Name of the city, e.g. 'Warsaw', 'London'.

    Returns:
        dict: status and weather report or error message.
    """
    try:
        geolocator = Nominatim(user_agent="city_weather_agent")
        location = geolocator.geocode(city)
        if not location:
            return {"status": "error", "error": f"Could not find location for city: {city}"}

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={location.latitude}&longitude={location.longitude}"
            f"&current=temperature_2m,weathercode,windspeed_10m"
            f"&wind_speed_unit=ms"
        )
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()["current"]

        return {
            "status": "success",
            "city": city,
            "temperature_c": data["temperature_2m"],
            "wind_speed_ms": data["windspeed_10m"],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


root_agent = Agent(
    name="weatherAgent",
    model="gemini-2.5-flash",
    description="Provides current weather information for any city.",
    instruction="You are a helpful weather assistant. Use the 'get_weather' tool to answer weather questions.",
    tools=[get_weather],
)
