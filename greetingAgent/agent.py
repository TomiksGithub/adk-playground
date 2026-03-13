from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents import Agent


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


root_agent = Agent(
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
