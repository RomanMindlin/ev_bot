from typing import Dict, Any
from amadeus import Client, ResponseError
from pydantic import BaseModel, HttpUrl
from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from ev_bot.settings import settings
from ev_bot.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger("ai_agent")

# Constants for the AI agent
MODEL = OpenAIModel(
    model_name="gpt-4-turbo-preview",
    provider=OpenAIProvider(
        api_key=settings.openai_key
    )
)
SYSTEM_PROMPT = """You are a helpful AI assistant that specializes in travel planning and booking.
Your job is to retrieve a list of flights available from the user's location, 
analyze the retrieved data, and return three best travel ideas.
Your responses should always be in valid JSON format.
You should analyze user requests and provide structured responses that can be used to make API calls.

You have access to the following tools:
- search_flight_inspiration: Searches for flight inspiration from the user's location for the next week.
  Returns a list of possible destinations with prices and other details."""


class TravelSummary(BaseModel):
    flight_number: str | None = None  # Optional for now if not available in mock
    flight_price: str
    starting_point: str
    destination: str
    travel_dates: str
    booking_link: HttpUrl


class TravelIdea(BaseModel):
    header: str
    motivation: str
    destination_description: str
    travel_summary: TravelSummary


class FlightAgentOutput(BaseModel):
    ideas: list[TravelIdea]


class AiAgent:
    """AI Agent for processing travel-related prompts using pydantic_ai."""
    
    def __init__(self):
        """Initialize the AI agent with model and system prompt."""
        logger.info("Initializing AiAgent")

        # Register the flight inspiration search tool
        logger.info("Registering flight inspiration search tool")
        tools = [
            Tool(self._search_flight_inspiration)
        ]

        self.agent = Agent(
            model=MODEL,
            tools=tools
        )
        self.amadeus = Client(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
        )

        logger.info("AiAgent initialized successfully")

    def _search_flight_inspiration(self) -> Dict[str, Any]:
        """
        Search for flight inspiration for the next week.
        
        Returns:
            Dict[str, Any]: Flight inspiration search results
        """
        logger.info("Searching for flight inspiration")
        # Calculate dates for next week
        today = datetime.now()
        departure_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        try:
            # Search for flight inspiration
            result = self.amadeus.shopping.flight_destinations.get(
                origin=settings.origin,
                oneWay=False,
                departureDate=departure_date,
                duration=7  # 7 days trip
            )
            logger.info(f"Found {len(result.get('data', []))} flight inspirations")
            return result
        except Exception as e:
            logger.error(f"Flight inspiration search failed: {str(e)}")
            raise
    
    async def run_agent(self, prompt: str) -> Dict[str, Any]:
        """
        Run the AI agent with the given prompt.
        
        Args:
            prompt (str): The user's prompt to process
            
        Returns:
            Dict[str, Any]: The agent's response as a dictionary
            
        Raises:
            ValueError: If the agent's response is not valid JSON
        """
        logger.info("Running AI agent with prompt")
        try:
            result = await self.agent.run(prompt)
            
            raw_output = result.output.strip()
            logger.debug(f"Raw agent output: {raw_output}")

            # Remove Markdown-style code block
            if raw_output.startswith("```json"):
                raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
            elif raw_output.startswith("```"):
                raw_output = raw_output.removeprefix("```").removesuffix("```").strip()

            structured = FlightAgentOutput.model_validate_json(raw_output)
            logger.info(f"Successfully processed {len(structured.ideas)} travel ideas")
            return structured
        except Exception as e:
            logger.error(f"Agent run failed: {str(e)}")
            raise
    