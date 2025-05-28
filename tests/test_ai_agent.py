import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from ev_bot.ai_agent import AiAgent, TravelSummary, TravelIdea, FlightAgentOutput


@pytest.fixture
def mock_amadeus_client():
    """Fixture for mocked AmadeusClient."""
    with patch("ev_bot.ai_agent.AmadeusClient") as mock:
        client = Mock()
        client.search_flight_inspiration.return_value = {
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
        mock.return_value = client
        yield client


@pytest.fixture
def mock_agent():
    """Fixture for mocked pydantic_ai Agent."""
    with patch("ev_bot.ai_agent.Agent") as mock:
        agent = Mock()
        agent.run = AsyncMock()
        agent.run.return_value = Mock(
            output='''{
                "ideas": [
                    {
                        "header": "London Adventure",
                        "motivation": "Perfect for history lovers",
                        "destination_description": "Explore the rich history of London",
                        "travel_summary": {
                            "flight_price": "500",
                            "starting_point": "NYC",
                            "destination": "LON",
                            "travel_dates": "2024-06-01 to 2024-06-08",
                            "booking_link": "https://test.com"
                        }
                    }
                ]
            }'''
        )
        mock.return_value = agent
        yield agent


@pytest.fixture
def ai_agent(mock_amadeus_client, mock_agent):
    """Fixture for AiAgent instance with mocked dependencies."""
    return AiAgent()


def test_ai_agent_initialization(ai_agent, mock_agent):
    """Test AiAgent initialization and tool registration."""
    # Verify agent was created with correct parameters
    mock_agent.assert_called_once()
    args, kwargs = mock_agent.call_args
    assert kwargs["model"] == "gpt-4-turbo-preview"
    assert "travel planning" in kwargs["system_prompt"]
    
    # Verify tool was registered
    mock_agent.return_value.register_tool.assert_called_once()
    args, kwargs = mock_agent.return_value.register_tool.call_args
    assert kwargs["name"] == "search_flight_inspiration"


def test_search_flight_inspiration(ai_agent, mock_amadeus_client):
    """Test flight inspiration search functionality."""
    result = ai_agent._search_flight_inspiration()
    
    # Verify AmadeusClient was called with correct parameters
    mock_amadeus_client.search_flight_inspiration.assert_called_once()
    args, kwargs = mock_amadeus_client.search_flight_inspiration.call_args
    assert kwargs["one_way"] is False
    assert kwargs["duration"] == 7
    
    # Verify result structure
    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["type"] == "flight-destination"


@pytest.mark.asyncio
async def test_run_agent_success(ai_agent, mock_agent):
    """Test successful agent run with valid JSON response."""
    result = await ai_agent.run_agent("test prompt")
    
    # Verify agent was called
    mock_agent.return_value.run.assert_called_once_with("test prompt")
    
    # Verify result structure
    assert isinstance(result, FlightAgentOutput)
    assert len(result.ideas) == 1
    assert result.ideas[0].header == "London Adventure"
    assert result.ideas[0].travel_summary.flight_price == "500"


@pytest.mark.asyncio
async def test_run_agent_invalid_json(ai_agent, mock_agent):
    """Test agent run with invalid JSON response."""
    mock_agent.return_value.run.return_value = Mock(
        output="invalid json"
    )
    
    with pytest.raises(Exception):
        await ai_agent.run_agent("test prompt")


@pytest.mark.asyncio
async def test_run_agent_markdown_json(ai_agent, mock_agent):
    """Test agent run with JSON in markdown code block."""
    mock_agent.return_value.run.return_value = Mock(
        output='''```json
        {
            "ideas": [
                {
                    "header": "London Adventure",
                    "motivation": "Perfect for history lovers",
                    "destination_description": "Explore the rich history of London",
                    "travel_summary": {
                        "flight_price": "500",
                        "starting_point": "NYC",
                        "destination": "LON",
                        "travel_dates": "2024-06-01 to 2024-06-08",
                        "booking_link": "https://test.com"
                    }
                }
            ]
        }
        ```'''
    )
    
    result = await ai_agent.run_agent("test prompt")
    assert isinstance(result, FlightAgentOutput)
    assert len(result.ideas) == 1 