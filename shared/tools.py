import datetime
import requests
from geopy.geocoders import Nominatim
from geopy.location import Location
from timezonefinder import TimezoneFinder
import pytz


def geocode(city: str) -> Location | None:
    """Return a geopy Location for a given city, or None if not found."""
    geolocator = Nominatim(user_agent="adk_shared_tools")
    return geolocator.geocode(city)


def get_timezone(city: str) -> str | None:
    """Return the IANA timezone string for a given city, or None if not found."""
    location = geocode(city)
    if not location:
        return None
    tf = TimezoneFinder()
    return tf.timezone_at(lng=location.longitude, lat=location.latitude)


def get_current_time(city: str) -> dict:
    """Get current time in provided city.

    Args:
        city: Name of the city, e.g. 'Warsaw', 'London'.

    Returns:
        dict: status and current time or error message.
    """
    try:
        timezone_str = get_timezone(city)
        if not timezone_str:
            return {"status": "error", "error": f"Could not determine timezone for city: {city}"}
        now = datetime.datetime.now(pytz.timezone(timezone_str))
        return {"status": "success", "city": city, "time": now.strftime("%I:%M %p")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_weather(city: str) -> dict:
    """Get current weather for a given city using the Open-Meteo API.

    Args:
        city: Name of the city, e.g. 'Warsaw', 'London'.

    Returns:
        dict: status and weather data or error message.
    """
    try:
        location = geocode(city)
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


def say_hello(name: str | None = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name: The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        print(f"--- Tool: say_hello called with name: {name} ---")
        return f"Hello, {name}!"
    print("--- Tool: say_hello called without a specific name ---")
    return "Hello there!"


def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    print("--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."
