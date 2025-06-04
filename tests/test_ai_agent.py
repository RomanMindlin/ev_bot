from unittest.mock import patch, Mock, AsyncMock
import pytest

# Global patches for all dependencies
patch_amadeus = patch("amadeus.Client")
patch_openai_model = patch("ev_bot.ai_agent.OpenAIModel")
patch_agent = patch("ev_bot.ai_agent.Agent")

mock_amadeus = patch_amadeus.start()
mock_openai = patch_openai_model.start()
mock_agent = patch_agent.start()

# Set up return values for mocks
mock_amadeus.return_value.shopping.flight_destinations.get.return_value = {
    "data": [
        {
            "type": "flight-destination",
            "origin": "NYC",
            "destination": "LON",
            "price": {"total": "500"},
            "links": {"flightOffers": "https://test.com"}
        }
    ]
}

# Create a mock response object that matches the Agent.run() return type
mock_response = Mock()
mock_response.output = '''{"ideas": [{"header": "London Adventure", "motivation": "Perfect for history lovers", "destination_description": "Explore the rich history of London", "travel_summary": {"flight_price": "500", "starting_point": "NYC", "destination": "LON", "travel_dates": "2024-06-01 to 2024-06-08", "booking_link": "https://test.com"}}]}'''

mock_agent_instance = Mock()
mock_agent_instance.run = AsyncMock(return_value=mock_response)
mock_agent.return_value = mock_agent_instance

from ev_bot.ai_agent import AiAgent, TravelSummary, TravelIdea, FlightAgentOutput

@pytest.fixture
def ai_agent():
    return AiAgent()

def test_ai_agent_initialization(ai_agent):
    """Test that AiAgent initializes correctly."""
    assert isinstance(ai_agent, AiAgent)
    assert hasattr(ai_agent, 'agent')
    assert hasattr(ai_agent, 'amadeus')

def test_search_flight_inspiration(ai_agent):
    """Test flight inspiration search."""
    result = ai_agent._search_flight_inspiration()
    assert result == {
        "data": [{
            "type": "flight-destination",
            "origin": "NYC",
            "destination": "LON",
            "price": {"total": "500"},
            "links": {"flightOffers": "https://test.com"}
        }]
    }

@pytest.mark.asyncio
async def test_run_agent_success(ai_agent):
    """Test successful agent run."""
    prompt = "Test prompt"
    result = await ai_agent.run_agent(prompt)
    assert isinstance(result, FlightAgentOutput)
    assert len(result.ideas) == 1
    assert result.ideas[0].header == "London Adventure"
    assert result.ideas[0].motivation == "Perfect for history lovers"

@pytest.mark.asyncio
async def test_run_agent_invalid_json(ai_agent):
    """Test agent run with invalid JSON response."""
    ai_agent.agent.run.return_value.output = "invalid json"
    with pytest.raises(Exception):
        await ai_agent.run_agent("test prompt")

@pytest.mark.asyncio
async def test_run_agent_markdown_json(ai_agent):
    """Test agent run with markdown-wrapped JSON response."""
    valid_json = '''{"ideas": [{"header": "London Adventure", "motivation": "Perfect for history lovers", "destination_description": "Explore the rich history of London", "travel_summary": {"flight_price": "500", "starting_point": "NYC", "destination": "LON", "travel_dates": "2024-06-01 to 2024-06-08", "booking_link": "https://test.com"}}]}'''
    ai_agent.agent.run.return_value.output = f"```json\n{valid_json}\n```"
    result = await ai_agent.run_agent("test prompt")
    assert isinstance(result, FlightAgentOutput)
    assert len(result.ideas) == 1 