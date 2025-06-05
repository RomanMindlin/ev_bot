import pytest
from unittest.mock import patch, AsyncMock
from ev_bot.telegram_sender import (
    send_to_telegram,
    format_travel_ideas,
    main,
    PROMPT
)

@pytest.mark.asyncio
async def test_send_to_telegram_success(mock_bot):
    """Test successful message sending to Telegram."""
    message = "Test message"
    with patch("ev_bot.telegram_sender.settings") as patched_settings:
        patched_settings.telegram_bot_token = "test_token"
        patched_settings.telegram_channel_id = "test_channel"
        await send_to_telegram(message)
        mock_bot.return_value.send_message.assert_called_once_with(
            chat_id="test_channel",
            text=message,
            parse_mode="HTML"
        )
        mock_bot.return_value.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_send_to_telegram_missing_settings():
    """Test sending message with missing Telegram settings."""
    with patch("ev_bot.telegram_sender.settings") as patched_settings:
        patched_settings.telegram_bot_token = None
        patched_settings.telegram_channel_id = None
        with pytest.raises(ValueError, match="Telegram bot token and channel ID must be configured"):
            await send_to_telegram("test message")

def test_format_travel_ideas(mock_flight_agent_output):
    """Test formatting travel ideas as HTML message."""
    message = format_travel_ideas(mock_flight_agent_output)
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
async def test_main_success(mock_bot, mock_flight_agent_output):
    """Test successful main function execution."""
    mock_bot.return_value.reset_mock()  # Reset mock to ensure clean state
    with patch("ev_bot.telegram_sender.AiAgent") as mock_ai_agent, \
         patch("ev_bot.telegram_sender.settings") as patched_settings:
        patched_settings.telegram_bot_token = "test_token"
        patched_settings.telegram_channel_id = "test_channel"
        mock_ai_agent.return_value.run_agent = AsyncMock(return_value=mock_flight_agent_output)
        await main()
        mock_bot.return_value.send_message.assert_called_once()
        args, kwargs = mock_bot.return_value.send_message.call_args
        assert kwargs["chat_id"] == "test_channel"
        assert "London Adventure" in kwargs["text"]

@pytest.mark.asyncio
async def test_main_agent_error():
    """Test main function with agent error."""
    with patch("ev_bot.telegram_sender.AiAgent") as mock_ai_agent:
        mock_ai_agent.return_value.run_agent.side_effect = Exception("Agent error")
        with pytest.raises(SystemExit) as exc_info:
            await main()
        assert exc_info.value.code == 1

@pytest.mark.asyncio
async def test_main_telegram_error(mock_bot):
    """Test main function with Telegram error."""
    mock_bot.return_value.send_message.side_effect = Exception("Telegram error")
    with pytest.raises(SystemExit) as exc_info:
        await main()
    assert exc_info.value.code == 1 