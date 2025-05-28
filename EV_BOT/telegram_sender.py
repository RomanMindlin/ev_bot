import asyncio
import sys
from typing import Dict, Any
from aiogram import Bot
from aiogram.enums import ParseMode
from ev_bot.settings import settings
from ev_bot.ai_agent import AiAgent


# Constant prompt for the AI agent
PROMPT = """Please analyze available flights and suggest three best travel ideas for the next week.
For each idea, provide:
1. A catchy header
2. Motivation for choosing this destination
3. Brief description of the destination
4. Travel details including flight price, dates, and booking link

Format the response as a JSON object with an 'ideas' array containing three travel ideas."""


async def send_to_telegram(message: str) -> None:
    """
    Send a message to the configured Telegram channel.
    
    Args:
        message (str): The message to send
        
    Raises:
        ValueError: If Telegram settings are not configured
    """
    if not settings.telegram_bot_token or not settings.telegram_channel_id:
        raise ValueError("Telegram bot token and channel ID must be configured")
    
    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(
            chat_id=settings.telegram_channel_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
    finally:
        await bot.session.close()


def format_travel_ideas(ideas: Dict[str, Any]) -> str:
    """
    Format travel ideas as an HTML message.
    
    Args:
        ideas (Dict[str, Any]): The travel ideas from the AI agent
        
    Returns:
        str: Formatted HTML message
    """
    message = "<b>🌟 Travel Ideas for Next Week 🌟</b>\n\n"
    
    for idea in ideas["ideas"]:
        message += f"<b>{idea['header']}</b>\n"
        message += f"<i>{idea['motivation']}</i>\n\n"
        message += f"{idea['destination_description']}\n\n"
        
        summary = idea["travel_summary"]
        message += "<b>Travel Details:</b>\n"
        message += f"📍 From: {summary['starting_point']}\n"
        message += f"✈️ To: {summary['destination']}\n"
        message += f"📅 Dates: {summary['travel_dates']}\n"
        message += f"💰 Price: {summary['flight_price']}\n"
        if summary.get("flight_number"):
            message += f"🔢 Flight: {summary['flight_number']}\n"
        message += f"🔗 <a href='{summary['booking_link']}'>Book Now</a>\n\n"
        message += "➖➖➖➖➖➖➖➖➖➖\n\n"
    
    return message


async def main() -> None:
    """Main function to run the telegram sender."""
    try:
        # Initialize AI agent
        agent = AiAgent()
        
        # Get travel ideas
        ideas = await agent.run_agent(PROMPT)
        
        # Format and send message
        message = format_travel_ideas(ideas)
        await send_to_telegram(message)
        
        print("Successfully sent travel ideas to Telegram channel")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 