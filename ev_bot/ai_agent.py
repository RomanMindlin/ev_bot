from typing import Dict, Any
from pydantic import BaseModel, HttpUrl, ValidationError
from pydantic_ai import Agent
from ev_bot.settings import settings
from ev_bot.amadeus_client import AmadeusClient
from ev_bot.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger("ai_agent")

# Constants for the AI agent
MODEL = "gpt-4-turbo-preview"
SYSTEM_PROMPT = """You are a helpful AI assistant that specializes in travel planning and booking.
Your job is to retrieve a list of flights available from the user's location, 
analyze the retrieved data, and return three best travel ideas.
Your responses should always be in valid JSON format.
You should analyze user requests and provide structured responses that can be used to make API calls.

You have access to the following tools:
- search_flight_inspiration: Searches for flight inspiration from the user's location for the next week.
  Returns a list of possible destinations with prices and other details."""

OPENAI_KEY = settings.openai_key


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
        self.agent = Agent(
            model=MODEL,
            system_prompt=SYSTEM_PROMPT,
            openai_key=OPENAI_KEY,
        )
        self.amadeus_client = AmadeusClient()
        
        # Register the flight inspiration search tool
        logger.info("Registering flight inspiration search tool")
        self.agent.register_tool(
            name="search_flight_inspiration",
            description="Search for flight inspiration from the user's location for the next week",
            function=self._search_flight_inspiration
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
        return_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        try:
            # Search for flight inspiration
            result = self.amadeus_client.search_flight_inspiration(
                origin=settings.origin,
                one_way=False,
                departure_date=departure_date,
                return_date=return_date,
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
    