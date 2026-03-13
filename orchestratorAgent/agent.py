import datetime
from geopy.geocoders import Nominatim
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


root_agent = Agent(
    name='orchestratorAgent',
    description='Orchestrator agent for the application.',
    instruction='Orchestrate the application and call the appropriate agents to answer the user\'s question.',
    tools=[get_current_time],
    model=Gemini(
        model_name='gemini-2.5-flash',
        retry_options=types.HttpRetryOptions(initial_delay=1, attempts=10),
    ),

)
