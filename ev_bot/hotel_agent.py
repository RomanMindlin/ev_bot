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
# from ev_bot.shared_tools import get_wikipedia_image

logger = setup_logger("hotel_agent")

# Constants for the AI agent
MODEL = OpenAIModel(
    model_name="gpt-4o-mini",
    provider=OpenAIProvider(
        api_key=settings.openai_key
    )
)

SYSTEM_PROMPT = f"""
You are a helpful AI hotel assistant.

Your task is to suggest 3 hotel offers based on available Amadeus API results.
Only suggest hotels with complete and valid information (name, address, price, rating).

Use the following tools:
- `search_hotel_offers`: returns hotel data based on city code and travel dates.

- Use structured format from output schema only
- Do not suggest duplicate hotel names or invalid entries

All text must be in **{settings.language}**, and all prices in **{settings.currency}**.
Return a single valid JSON response (no markdown or explanation).
"""


class HotelSummary(BaseModel):
    hotel_name: str = Field(description="Name of the hotel")
    address: str = Field(description="Full address of the hotel")
    rating: Optional[str] = Field(default=None, description="Star rating or customer rating")
    total_price: str = Field(description="Total price for the entire stay")
    check_in_date: datetime = Field(description="Check-in date")
    check_out_date: datetime = Field(description="Check-out date")
    booking_link: HttpUrl = Field(description="Link to book the hotel")
    # image_url: Optional[HttpUrl] = Field(default=None, description="Image URL of the hotel or location")


class HotelSearchResult(BaseModel):
    city_name: str = Field(description="City where the hotel is located")
    city_code: str = Field(description="IATA city code")
    hotels: list[HotelSummary]


class HotelAgent:
    """AI Agent for hotel search prompts using pydantic_ai."""

    def __init__(self):
        logger.info("Initializing HotelAgent")

        tools = [
            Tool(self._search_hotel_offers),
            # Tool(get_wikipedia_image)
        ]

        self.agent = Agent(
            model=MODEL,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            output_type=HotelSearchResult
        )

        self.amadeus = Client(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            hostname=settings.environment
        )

        logger.info("HotelAgent initialized successfully")

    def _search_hotel_offers(self, city_code: str, check_in: str, check_out: str) -> Dict[str, Any] | None:
        logger.info(f"Searching for hotel offers in {city_code} from {check_in} to {check_out}")
        MAX_RETRIES = 3
        DELAY_SECONDS = 1
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                hotels = self.amadeus.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code,
                    radius=5,
                    radiusUnit='KM',
                    ratings=['2', '3', '4'],
                    hotelSource='ALL'
                )
                hotel_codes = [hotel['hotelId'] for hotel in hotels.data]

                result = self.amadeus.shopping.hotel_offers_search.get(
                    hotelIds=hotel_codes,
                    checkInDate=check_in,
                    checkOutDate=check_out,
                    adults=2,
                    paymentPolicy='NONE',
                    includeClosed=False,
                    bestRateOnly=True
                )
                logger.info(f"Found {len(result.data)} hotel offers")
                return result.data
            except ResponseError as e:
                logger.error(f"Hotel offers search failed with status {e.response.status_code}: {e.response.body}")
                return None

    async def run_agent(self, prompt: str) -> HotelSearchResult:
        logger.info("Running HotelAgent with prompt")
        try:
            result = await self.agent.run(prompt)
            if isinstance(result.output, HotelSearchResult):
                return result.output

            raw_output = str(result.output).strip()
            if raw_output.startswith("```json"):
                raw_output = raw_output.removeprefix("```json").removesuffix("```").strip()
            elif raw_output.startswith("```"):
                raw_output = raw_output.removeprefix("```").removesuffix("```").strip()

            return HotelSearchResult.model_validate_json(raw_output)
        except Exception as e:
            logger.error(f"HotelAgent run failed: {str(e)}")
            raise
