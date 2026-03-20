from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from shared.tools import get_weather, get_current_time

root_agent = Agent(
    name="timeAndWeatherAgent",
    description="Agent to answer questions about the current time and weather in any city.",
    instruction="You are a helpful agent who can answer user questions about the current time and weather in any city.",
    tools=[get_current_time, get_weather],
    model=Gemini(
        model_name="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(initial_delay=1, attempts=10),
    ),
)
