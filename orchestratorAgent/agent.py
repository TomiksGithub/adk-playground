import datetime
import requests
from pathlib import Path
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from timezonefinder import TimezoneFinder
import pytz
from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types



def get_timezone(city: str) -> str | None:
    """Return the IANA timezone string for a given city, or None if not found."""
    geolocator = Nominatim(user_agent="city_time_agent")
    location = geolocator.geocode(city)
    if not location:
        return None
    tf = TimezoneFinder()
    return tf.timezone_at(lng=location.longitude, lat=location.latitude)


def get_current_time(city: str) -> dict:
    """Get current time in provided city."""
    try:
        timezone_str = get_timezone(city)
        if not timezone_str:
            return {"status": "error", "error": f"Could not determine timezone for city: {city}"}

        now = datetime.datetime.now(pytz.timezone(timezone_str))
        time_str = now.strftime('%I:%M %p')
        return {"status": "success", "city": city, "timea": time_str}
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
    name='orchestratorAgent',
    description='Orchestrator agent for the application.',
    instruction='Orchestrate the application and call the appropriate agents to answer the user\'s question.',
    tools=[get_current_time, get_weather],
    model=Gemini(
        model_name='gemini-2.5-flash',
        retry_options=types.HttpRetryOptions(initial_delay=1, attempts=10),
    ),

)
