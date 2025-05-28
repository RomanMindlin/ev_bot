import pytest
from unittest.mock import Mock, patch, AsyncMock
from ev_bot.telegram_sender import (
    send_to_telegram,
    format_travel_ideas,
    main,
    PROMPT
)


@pytest.fixture
def mock_bot():
    """Fixture for mocked aiogram Bot."""
    with patch("ev_bot.telegram_sender.Bot") as mock:
        bot = Mock()
        bot.send_message = AsyncMock()
        mock.return_value = bot
        yield bot


@pytest.fixture
def mock_ai_agent():
    """Fixture for mocked AiAgent."""
    with patch("ev_bot.telegram_sender.AiAgent") as mock:
        agent = Mock()
        agent.run_agent = AsyncMock()
        agent.run_agent.return_value = {
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
        mock.return_value = agent
        yield agent


@pytest.fixture
def mock_settings():
    """Fixture for mocked settings."""
    with patch("ev_bot.telegram_sender.settings") as mock:
        mock.telegram_bot_token = "test_token"
        mock.telegram_channel_id = "test_channel"
        yield mock


@pytest.mark.asyncio
async def test_send_to_telegram_success(mock_bot, mock_settings):
    """Test successful message sending to Telegram."""
    message = "Test message"
    await send_to_telegram(message)
    
    # Verify bot was created and message was sent
    mock_bot.assert_called_once_with(token="test_token")
    mock_bot.return_value.send_message.assert_called_once_with(
        chat_id="test_channel",
        text=message,
        parse_mode="HTML"
    )
    mock_bot.return_value.session.close.assert_called_once()


@pytest.mark.asyncio
async def test_send_to_telegram_missing_settings(mock_bot):
    """Test sending message with missing Telegram settings."""
    with patch("ev_bot.telegram_sender.settings") as mock_settings:
        mock_settings.telegram_bot_token = None
        mock_settings.telegram_channel_id = None
        
        with pytest.raises(ValueError, match="Telegram bot token and channel ID must be configured"):
            await send_to_telegram("test message")


def test_format_travel_ideas():
    """Test formatting travel ideas as HTML message."""
    ideas = {
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
    
    message = format_travel_ideas(ideas)
    
    # Verify message format
    assert "🌟 Travel Ideas for Next Week 🌟" in message
    assert "London Adventure" in message
    assert "Perfect for history lovers" in message
    assert "Explore the rich history of London" in message
    assert "NYC" in message
    assert "LON" in message
    assert "500" in message
    assert "https://test.com" in message
    assert "<b>" in message
    assert "<i>" in message
    assert "<a href=" in message


@pytest.mark.asyncio
async def test_main_success(mock_ai_agent, mock_bot, mock_settings):
    """Test successful main function execution."""
    await main()
    
    # Verify AI agent was called with correct prompt
    mock_ai_agent.return_value.run_agent.assert_called_once_with(PROMPT)
    
    # Verify message was sent
    mock_bot.return_value.send_message.assert_called_once()
    args, kwargs = mock_bot.return_value.send_message.call_args
    assert kwargs["chat_id"] == "test_channel"
    assert "London Adventure" in kwargs["text"]


@pytest.mark.asyncio
async def test_main_agent_error(mock_ai_agent, mock_bot, mock_settings):
    """Test main function with AI agent error."""
    mock_ai_agent.return_value.run_agent.side_effect = Exception("Agent error")
    
    with pytest.raises(SystemExit) as exc_info:
        await main()
    
    assert exc_info.value.code == 1
    mock_bot.return_value.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_main_telegram_error(mock_ai_agent, mock_bot, mock_settings):
    """Test main function with Telegram sending error."""
    mock_bot.return_value.send_message.side_effect = Exception("Telegram error")
    
    with pytest.raises(SystemExit) as exc_info:
        await main()
    
    assert exc_info.value.code == 1 