import json
import requests
from typing import Dict, Any, Optional
from amadeus import Client, ResponseError
from pydantic import BaseModel, HttpUrl, Field
from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from ev_bot.settings import settings
from ev_bot.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger("ai_agent")

# Constants for the AI agent
MODEL = OpenAIModel(
    model_name="gpt-4o-mini",
    provider=OpenAIProvider(
        api_key=settings.openai_key
    )
)
SYSTEM_PROMPT = f"""
You are a helpful AI travel assistant.

Your task is to suggest three compelling travel ideas based on available flights from the user's location.
Prioritize destinations that are cheap, interesting, or unique. 
Each idea must highlight a distinct destination — do not suggest multiple ideas for the same city or similar locations.
Ensure the destinations differ clearly in geography, culture, or travel experience.

You can use:
- `search_flight_inspiration`: returns flight data (price, route, dates).
  Do not use destinations with invalid or unknown IATA codes (e.g., YJB, XOC, train stations, or test codes).
  Use only real **airport** codes that can be mapped to known **city names**.
  Decode both 'origin' and 'destination' codes to city names.
- `get_wikipedia_image`: returns a representative image of a city.

For each idea:
- Include destination image using `get_wikipedia_image`
- Use the structured format defined by the output schema
- Provide catchy title, travel motivation, and short destination description

Respond with **valid JSON only** — no markdown or commentary.

All text must be in **{settings.language}**, and all prices in **{settings.currency}**.
"""


class TravelSummary(BaseModel):
    flight_number: str | None = Field(
        default=None,
        description="Flight number (optional)"
    )
    flight_price: str = Field(
        description="Price of the flight tickets"
    )
    starting_point: str = Field(
        description="City name for origin"
    )
    destination: str = Field(
        description="City name for destination"
    )
    travel_dates: str = Field(
        description="Travel dates as a string"
    )
    booking_link: HttpUrl = Field(
        description="URL to purchase the flight tickets"
    )


class TravelIdea(BaseModel):
    header: str = Field(
        description="A catchy title for the travel idea"
    )
    motivation: str = Field(
        description="A reason or hook for visiting the destination"
    )
    destination_description: str = Field(
        description="A short description of the destination"
    )
    travel_summary: TravelSummary
    image_url: Optional[HttpUrl] = Field(
        default=None,
        description="A URL pointing to an image of the destination"
    )


class FlightAgentOutput(BaseModel):
    ideas: list[TravelIdea]


def get_wikipedia_image(destination: str) -> Optional[str]:
    """
    Retrieves a thumbnail image URL for a travel destination from Wikipedia.

    Args:
        destination (str): Name of the city or point of interest.

    Returns:
        str | None: Image URL if found, otherwise None.
    """
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": destination,
        "prop": "pageimages",
        "pithumbsize": 600
    }
    logger.info(f"Fetching Wikipedia image for: {destination}")
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        for page in pages.values():
            if "thumbnail" in page:
                logger.info(f"Found image URL: {page['thumbnail']['source']}")
                return page["thumbnail"]["source"]
    except requests.RequestException as e:
        logger.error(f"Wikipedia image search failed: {e}")
    logger.info(f"Image not found for destination: {destination}")
    return None


class AiAgent:
    """AI Agent for processing travel-related prompts using pydantic_ai."""

    def __init__(self):
        """Initialize the AI agent with model and system prompt."""
        logger.info("Initializing AiAgent")

        # Register the flight inspiration search tool
        logger.info("Registering flight inspiration search tool")
        tools = [
            Tool(self._search_flight_inspiration),
            Tool(get_wikipedia_image)
        ]

        self.agent = Agent(
            model=MODEL,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            output_type=FlightAgentOutput
        )
        self.amadeus = Client(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            hostname=settings.environment
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
                nonStop=True,
                departureDate=departure_date
            )
            logger.info(f"Found {len(result.data)} flight inspirations")
            return result.data
        except ResponseError as e:
            logger.error(f"Flight inspiration search failed with status {e.response.status_code}: {e.response.body}")
            # raise

        # Fallback to sample data
        logger.warning("Falling back to sample data from debug_samples/inspiration_API_sample.json")
        try:
            with open("../debug_samples/inspiration_API_sample.json", "r", encoding="utf-8") as f:
                sample = json.load(f)
            return sample.get("data", [])
        except Exception as fallback_error:
            logger.critical(f"Failed to load sample data: {str(fallback_error)}")
            raise RuntimeError("Flight search failed and sample data could not be loaded.") from fallback_error

    async def run_agent(self, prompt: str) -> FlightAgentOutput:
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
        logger.info(f"Prompt passed to agent: {prompt}")
        try:
            result = await self.agent.run(prompt)

            if isinstance(result.output, FlightAgentOutput):
                structured = result.output
            else:
                # Otherwise, treat as string and parse
                raw_output = str(result.output).strip()
                logger.info(f"Raw agent output: {raw_output}")

                # Remove Markdown-style code block
                if raw_output.startswith("```json"):
                    raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
                elif raw_output.startswith("```"):
                    raw_output = raw_output.removeprefix("```").removesuffix("```").strip()

                structured = FlightAgentOutput.model_validate_json(raw_output)

            logger.info(f"Successfully processed {len(structured.ideas)} travel ideas")
            logger.info(f"Parsed travel ideas: {structured.model_dump_json(indent=2)}")
            return structured
        except Exception as e:
            logger.error(f"Agent run failed: {str(e)}")
            raise
