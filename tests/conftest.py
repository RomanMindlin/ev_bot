import os
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Set test environment variables before any imports
os.environ["OPENAI_API_KEY"] = "test_openai_key"

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests."""
    with patch("ev_bot.settings") as mock_settings:
        mock_settings.openai_key = "test_openai_key"
        mock_settings.client_id = "test_client_id"
        mock_settings.client_secret = "test_client_secret"
        mock_settings.origin = "NYC"
        mock_settings.telegram_bot_token = "test_token"
        mock_settings.telegram_channel_id = "test_channel"
        yield mock_settings

@pytest.fixture
def mock_amadeus_client():
    """Mock Amadeus client."""
    with patch("ev_bot.ai_agent.Client") as mock_client:
        mock_client.return_value.shopping.flight_destinations.get.return_value = {
            "data": [{
                "type": "flight-destination",
                "origin": "NYC",
                "destination": "LON",
                "price": {"total": "500"},
                "links": {"flightOffers": "https://test.com"}
            }]
        }
        yield mock_client

@pytest.fixture
def mock_openai_model():
    """Mock OpenAI model."""
    with patch("ev_bot.ai_agent.OpenAIModel") as mock_model:
        yield mock_model

@pytest.fixture
def mock_agent():
    """Mock Agent class."""
    with patch("ev_bot.ai_agent.Agent") as mock_agent:
        mock_response = Mock()
        mock_response.output = '''{"ideas": [{"header": "London Adventure", "motivation": "Perfect for history lovers", "destination_description": "Explore the rich history of London", "travel_summary": {"flight_price": "500", "starting_point": "NYC", "destination": "LON", "travel_dates_str": "2024-06-01 to 2024-06-08", "booking_link": "https://test.com"}}]}'''
        mock_agent_instance = Mock()
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        mock_agent.return_value = mock_agent_instance
        yield mock_agent

@pytest.fixture
def mock_bot():
    """Mock Telegram Bot."""
    with patch("ev_bot.telegram_sender.Bot") as mock_bot:
        mock_bot_instance = Mock()
        mock_bot_instance.send_message = AsyncMock()
        mock_bot_instance.session.close = AsyncMock()
        mock_bot.return_value = mock_bot_instance
        yield mock_bot

@pytest.fixture
def ai_agent():
    with patch("ev_bot.ai_agent.Client") as mock_client, \
         patch("ev_bot.ai_agent.OpenAIModel") as mock_openai_model, \
         patch("ev_bot.ai_agent.Agent") as mock_agent:
        from pydantic import HttpUrl
        from ev_bot.ai_agent import AiAgent, TravelIdea, TravelSummary, FlightAgentOutput
        # Setup mock for Amadeus
        mock_client.return_value.shopping.flight_destinations.get.return_value = {
            "data": [{
                "type": "flight-destination",
                "origin": "NYC",
                "destination": "LON",
                "price": {"total": "500"},
                "links": {"flightOffers": "https://test.com"}
            }]
        }
        # Setup mock for Agent
        mock_response = Mock()
        mock_response.output = '''{"ideas": [{"header": "London Adventure", "motivation": "Perfect for history lovers", "destination_description": "Explore the rich history of London", "travel_summary": {"flight_price": "500", "starting_point": "NYC", "destination": "LON", "travel_dates_str": "2024-06-01 to 2024-06-08", "booking_link": "https://test.com"}}]}'''
        mock_agent_instance = Mock()
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        mock_agent.return_value = mock_agent_instance
        return AiAgent()

@pytest.fixture
def mock_flight_agent_output():
    from pydantic import HttpUrl
    from ev_bot.ai_agent import FlightAgentOutput, TravelIdea, TravelSummary
    mock_travel_summary = TravelSummary(
        flight_price="500",
        starting_point="NYC",
        destination="LON",
        travel_dates_str="2024-06-01 to 2024-06-08",
        travel_start_date=datetime("2024-06-01"),
        travel_end_date=datetime("2024-06-08"),
        booking_link=HttpUrl("https://test.com")
    )
    mock_travel_idea = TravelIdea(
        header="London Adventure",
        motivation="Perfect for history lovers",
        destination_description="Explore the rich history of London",
        travel_summary=mock_travel_summary
    )
    return FlightAgentOutput(ideas=[mock_travel_idea]) 