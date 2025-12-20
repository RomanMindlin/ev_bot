from typing import Dict, Any
from amadeus import Client as AmadeusClient, ResponseError
from travelpayouts import Client as TravelPayoutsClient
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
    model_name="gpt-4o-mini",
    provider=OpenAIProvider(
        api_key=settings.openai_key
    )
)
SYSTEM_PROMPT = """You are a helpful AI assistant that specializes in travel planning and booking.
Your job is to retrieve a list of flights available from the user's location, 
analyze the retrieved data, and return best travel ideas.

You have access to the following tools:
- search_flight_inspiration: Searches for flight inspiration from the user's location for the next week.
  Returns a list of possible destinations with prices and other details.
- search_hotel_offers: Searches for hotel offers in a specific city for given dates.
  Returns a list of available hotels with prices and details.
  Returns None if no hotels are found for the given city and dates.

Your task is to:
1. First, get flight inspirations and analyze them to find the best travel options
2. For each potential travel idea, search for hotels using the destination city code and travel dates
3. If hotels are found (result is not None), include the best hotel option in the travel idea
4. If no hotels are found (result is None), try another destination until you have 3 complete travel ideas
5. Don't try to search for hotels in the same city more than once
6. If you can't find hotels for enough destinations, include the remaining ideas without hotels to complete the list of 3
7. Don't stop until yuo have at least 3 complete travel ideas with all required information or no ideas left to process

Each travel idea must follow this structure:
        {
          "header": "...", #a catchy travel idea title
          "motivation": "...", #a reason to visit the destination
          "destination_description": "...", #a brief about the location
          "travel_summary": {
            "flight_number": "...", #if available
            "flight_price": "...", 
            "starting_point": "...", #city name for origin code
            "destination": "...", #city name for destination code
            "travel_dates_str": "...", #travel dates as a string
            "travel_start_date": "...", #travel start date
            "travel_end_date": "...", #travel end date
            "booking_link": "...", #URL to purchase tickets
            "hotel": {
              "name": "...", #hotel name
              "price": "...", #hotel price per night
              "rating": "...", #hotel rating
              "address": "...", #hotel address
              "booking_link": "..." #URL to book the hotel
            }
          }
        }
    
Return a JSON object with a top-level "ideas" key containing a list of ideas.

Return only valid JSON. Do not include any markdown, code block delimiters, or extra commentary.
  """


class HotelInfo(BaseModel):
    name: str
    price: str
    rating: str
    address: str
    booking_link: HttpUrl


class TravelSummary(BaseModel):
    flight_number: str | None = None  # Optional for now if not available in mock
    flight_price: str
    starting_point: str
    destination: str
    travel_dates_str: str
    travel_start_date: datetime
    travel_end_date: datetime
    booking_link: HttpUrl
    hotel: HotelInfo | None = None


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

        # Register the tools
        logger.info("Registering tools")
        tools = [
            Tool(self._search_flight_inspiration),
            Tool(self._search_hotel_offers)
        ]

        self.agent = Agent(
            model=MODEL,
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            output_type=FlightAgentOutput
        )
        self.amadeus = AmadeusClient(
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            hostname=settings.environment
        )
        self.travelpayouts = TravelPayoutsClient(
            settings.travelpayouts_token,
            settings.travelpayouts_marker
        )

        logger.info("AiAgent initialized successfully")

    def _search_hotel_offers(self, city_code: str, check_in: str, check_out: str) -> Dict[str, Any] | None:
        """
        Search for hotel offers in a specific city for given dates.
        
        Args:
            city_code (str): The city code to search in
            check_in (str): Check-in date in YYYY-MM-DD format
            check_out (str): Check-out date in YYYY-MM-DD format
            
        Returns:
            Dict[str, Any]: Hotel offers search results
        """
        logger.info(f"Searching for hotel offers in {city_code} from {check_in} to {check_out}")
        try:
            hotels = self.amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code,
                radius=5,
                radiusUnit='KM',
                # ratings=['2', '3', '4'],
                hotelSource='ALL'
            )

            hotel_codes = [hotel['hotelId'] for hotel in hotels.data[:20]]

            result = self.amadeus.shopping.hotel_offers_search.get(
                hotelIds=hotel_codes,
                checkInDate=check_in,
                checkOutDate=check_out,
                currency=settings.currency or 'EUR',
                adults=2,
                paymentPolicy='NONE',
                includeClosed=False,
                bestRateOnly=True
            )
            logger.info(f"Found {len(result.data)} hotel offers")
            
            summarized = []
            for hotel in result.data[:3]:
                offer = hotel['offers'][0] if hotel.get('offers') else None
                if offer and offer.get('price', {}).get('total'):
                    summarized.append({
                        'name': hotel.get('hotel', {}).get('name', 'Unknown'),
                        'price': offer.get('price', {}).get('total'),
                        'currency': offer.get('price', {}).get('currency', 'EUR'),
                        'checkIn': offer.get('checkInDate'),
                        'checkOut': offer.get('checkOutDate')
                    })
            
            return summarized if summarized else None
        except ResponseError as e:
            logger.error(f"Hotel offers search failed with status {e.response.status_code}: {e.response.body}")
            return None

    def _search_flight_inspiration(self) -> Dict[str, Any]:
        """
        Search for flight inspiration for the next week using TravelPayouts API.
        
        Returns:
            Dict[str, Any]: Flight inspiration search results
        """
        logger.info("Searching for flight inspiration")
        # Calculate dates for next week
        today = datetime.now()
        departure_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        return_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

        try:
            # Use prices_for_dates to get flight prices for various destinations
            # This doesn't require a destination - it returns prices for multiple destinations
            result = self.travelpayouts.prices_for_dates(
                origin=settings.origin,
                departure_at=departure_date,
                return_at=return_date,
                currency=settings.currency or 'EUR',
                unique=True,
                limit=10
            )
            
            # Handle different response formats
            if isinstance(result, dict):
                data = result.get('data', result)
            else:
                data = result
            
            # Ensure we return a list
            if not isinstance(data, list):
                data = [data] if data else []
            
            summarized = []
            for flight in data:
                summarized.append({
                    'origin': flight.get('origin'),
                    'destination': flight.get('destination'),
                    'departure_at': flight.get('departure_at'),
                    'return_at': flight.get('return_at'),
                    'price': flight.get('value') or flight.get('price'),
                    'airline': flight.get('airline'),
                    'flight_number': flight.get('flight_number')
                })
            
            logger.info(f"Found {len(summarized)} flight inspirations")
            return summarized
        except Exception as e:
            logger.error(f"Flight inspiration search failed: {str(e)}")
            raise
    
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
        try:
            result = await self.agent.run(prompt)

            if isinstance(result.output, FlightAgentOutput):
                structured = result.output
            else:
                # Otherwise, treat as string and parse
                raw_output = str(result.output).strip()
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
    