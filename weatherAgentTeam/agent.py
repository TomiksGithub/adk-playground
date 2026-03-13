import requests
from pathlib import Path
from typing import Optional
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


def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name: The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        return f"Hello, {name}!"
    return "Hello there!"


def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    return "Goodbye! Have a great day."


greeting_agent = Agent(
    name="greeting_agent",
    model="gemini-2.5-flash",
    description="Handles simple greetings and hellos using the 'say_hello' tool.",
    instruction=(
        "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
        "Use the 'say_hello' tool to generate the greeting. "
        "If the user provides their name, make sure to pass it to the tool. "
        "Do not engage in any other conversation or tasks."
    ),
    tools=[say_hello],
)

farewell_agent = Agent(
    name="farewell_agent",
    model="gemini-2.5-flash",
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
    instruction=(
        "You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
        "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
        "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
        "Do not perform any other actions."
    ),
    tools=[say_goodbye],
)

root_agent = Agent(
    name="weather_agent_v2",
    model="gemini-2.5-flash",
    description="The main coordinator agent. Handles weather requests and delegates greetings/farewells to specialists.",
    instruction=(
        "You are the main Weather Agent coordinating a team. Your primary responsibility is to provide weather information. "
        "Use the 'get_weather' tool ONLY for specific weather requests (e.g., 'weather in London'). "
        "You have specialized sub-agents: "
        "1. 'greeting_agent': Handles simple greetings like 'Hi', 'Hello'. Delegate to it for these. "
        "2. 'farewell_agent': Handles simple farewells like 'Bye', 'See you'. Delegate to it for these. "
        "Analyze the user's query. If it's a greeting, delegate to 'greeting_agent'. "
        "If it's a farewell, delegate to 'farewell_agent'. "
        "If it's a weather request, handle it yourself using 'get_weather'. "
        "For anything else, respond appropriately or state you cannot handle it."
    ),
    tools=[get_weather],
    sub_agents=[greeting_agent, farewell_agent],
)
