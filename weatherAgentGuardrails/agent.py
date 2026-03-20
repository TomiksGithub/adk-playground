from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .tools import get_weather_stateful, say_hello, say_goodbye
from .callbacks import block_keyword_guardrail, block_paris_tool_guardrail

MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"
MODEL_GPT_4O = "openai/gpt-4.1"
MODEL_CLAUDE_SONNET = "claude-sonnet-4-6"

greeting_agent = Agent(
    name="greeting_agent",
    model=MODEL_GEMINI_2_5_FLASH,
    description="Handles simple greetings and hellos using the 'say_hello' tool.",
    instruction=(
        "You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. "
        "If the user provides their name, pass it to the tool. Do nothing else."
    ),
    tools=[say_hello],
)

farewell_agent = Agent(
    name="farewell_agent",
    model=MODEL_GEMINI_2_5_FLASH,
    description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
    instruction=(
        "You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye' tool. "
        "Do not perform any other actions."
    ),
    tools=[say_goodbye],
)

root_agent = Agent(
    name="weather_agent_v6_tool_guardrail",
    model=MODEL_GEMINI_2_5_FLASH,
    description="Main agent: Handles weather, delegates greetings/farewells, includes input AND tool guardrails.",
    instruction=(
        "You are the main Weather Agent. Provide weather using 'get_weather_stateful'. "
        "Delegate greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
        "Handle only weather, greetings, and farewells."
    ),
    tools=[get_weather_stateful],
    sub_agents=[greeting_agent, farewell_agent],
    output_key="last_weather_report",
    before_model_callback=block_keyword_guardrail,
    before_tool_callback=block_paris_tool_guardrail,
)
