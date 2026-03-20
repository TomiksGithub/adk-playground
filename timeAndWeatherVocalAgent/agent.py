from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents import Agent
from shared.tools import get_weather, get_current_time

root_agent = Agent(
    name="timeAndWeatherVocalAgent",
    model="gemini-2.5-flash-native-audio-latest",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    #tools=[get_weather, get_current_time],
    tools=[],
)