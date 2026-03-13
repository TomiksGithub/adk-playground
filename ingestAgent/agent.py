from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from google.adk.agents.llm_agent import Agent

ingestAgent = Agent(
    model='gemini-2.5-flash',
    name='ingestAgent',
    description='Ingest agent for the application.',
    instruction='Ingest the data from the source and store for further processing.',
)
