import asyncio
import sys
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from ev_bot.settings import settings
# from ev_bot.flight_agent import AiAgent, FlightAgentOutput
from ev_bot.logger import setup_logger
from typing import List, Tuple, Optional
from ev_bot.agent_orchestration import agent_orchestration

logger = setup_logger("telegram_sender")

# Constant prompt for the AI agent
PROMPT = """Give me best travel ideas"""


def is_direct_image_url(url: str) -> bool:
    """
    Check if the URL points directly to a supported image format.
    """
    return url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))


async def send_to_telegram(formatted_ideas: List[Tuple[Optional[str], str]]) -> None:
    """
    Send a message to the configured Telegram channel.
    
    Args:
        formatted_ideas (List[Tuple[Optional[str], str]]): List of (image_url, message) pairs.
        
    Raises:
        ValueError: If Telegram settings are not configured
    """
    if not settings.telegram_bot_token or not settings.telegram_channel_id:
        logger.error("Telegram settings not configured")
        raise ValueError("Telegram bot token and channel ID must be configured")

    logger.info("Sending message to Telegram channel")
    bot = Bot(token=settings.telegram_bot_token)

    try:
        for image_url, message in formatted_ideas:
            try:
                if not image_url:
                    logger.info("No image URL provided for idea")
                    raise ValueError("Missing image URL")

                if not is_direct_image_url(str(image_url)):
                    logger.info(f"Image URL rejected (not a direct image): {image_url}")
                    raise ValueError("Unsupported image format")

                await bot.send_photo(
                    chat_id=settings.telegram_channel_id,
                    photo=str(image_url),
                    caption=message,
                    parse_mode=ParseMode.HTML
                )
                logger.info("Sent photo + caption")

            except TelegramBadRequest as tg_err:
                if "wrong type of the web page content" in str(tg_err):
                    logger.error(f"Telegram rejected image URL due to bad content: {image_url}")
                else:
                    logger.error(f"TelegramBadRequest: {tg_err}")
                logger.warning("Falling back to text message")
                await bot.send_message(
                    chat_id=settings.telegram_channel_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                logger.info("Sent text message")

            except Exception as e:
                logger.warning(f"Falling back to text message due to exception: {e}")
                if image_url:
                    logger.debug(f"Problematic image URL: {image_url}")
                await bot.send_message(
                    chat_id=settings.telegram_channel_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                logger.info("Sent text message")

    finally:
        await bot.session.close()


def format_combined_ideas(combined_suggestions: List[dict]) -> List[Tuple[Optional[str], str]]:
    """
    Format combined flight + hotel suggestions into HTML messages.
    """
    formatted = []

    logger.info(f"Formatting {len(combined_suggestions)} travel ideas")

    for idx, entry in enumerate(combined_suggestions, start=1):
        idea = entry["travel_idea"]
        hotels = entry["hotels"]

        logger.info(f"Formatting idea #{idx}: {idea.get('header')} → {idea['travel_summary']['destination']}")

        message = f"<b>{idea['header']}</b>\n"
        message += f"<i>{idea['motivation']}</i>\n\n"
        message += f"{idea['destination_description']}\n\n"

        summary = idea["travel_summary"]
        message += "<b>Travel Details:</b>\n"
        message += f"📍 From: {summary['starting_point']}\n"
        message += f"✈️ To: {summary['destination']}\n"
        message += f"📅 Dates: {summary['travel_dates']}\n"
        message += f"💰 Price: {summary['flight_price']} {settings.currency}\n"
        if summary.get("flight_number"):
            message += f"🔢 Flight: {summary['flight_number']}\n"
        message += f"🔗 <a href='{summary['booking_link']}'>Book Flight</a>\n\n"

        if hotels:
            message += "<b>🏨 Hotel Options:</b>\n"
            for hotel in hotels:
                message += f"• {hotel['hotel_name']} ({hotel.get('rating', 'N/A')}⭐)\n"
                message += f"  💵 {hotel['total_price']} {settings.currency}\n"
                message += f"  📍 {hotel['address']}\n"
                message += f"  🔗 <a href='{hotel['booking_link']}'>Book Hotel</a>\n\n"
        else:
            logger.warning(f"No hotels found for destination: {summary['destination']} ({summary['destination_code']})")
            message += "⚠️ No hotel offers found.\n"

        formatted.append((idea.get("image_url"), message))

    logger.info("Message formatting completed")
    return formatted


async def main() -> None:
    """Main function to run the telegram sender."""
    try:
        logger.info("Starting telegram sender")

        logger.info("Running multi-agent travel LangGraph")
        result = await agent_orchestration(PROMPT)

        logger.info("Formatting travel + hotel ideas for Telegram")
        formatted_ideas = format_combined_ideas(result["combined_suggestions"])

        logger.info(f"Sending {len(formatted_ideas)} messages to Telegram")
        await send_to_telegram(formatted_ideas)

        logger.info("Successfully completed telegram sender execution")
        print("Successfully sent travel and hotel ideas to Telegram channel")

    except Exception as e:
        logger.error(f"Error in telegram sender: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
