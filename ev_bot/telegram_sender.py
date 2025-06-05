import asyncio
import sys
from aiogram import Bot
from aiogram.enums import ParseMode
from ev_bot.settings import settings
from ev_bot.ai_agent import AiAgent, FlightAgentOutput
from ev_bot.logger import setup_logger


logger = setup_logger("telegram_sender")


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
        logger.error("Telegram settings not configured")
        raise ValueError("Telegram bot token and channel ID must be configured")
    
    logger.info("Sending message to Telegram channel")
    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(
            chat_id=settings.telegram_channel_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        logger.info("Message sent successfully")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise
    finally:
        await bot.session.close()


def format_travel_ideas(ideas: FlightAgentOutput) -> str:
    """
    Format travel ideas as an HTML message.
    
    Args:
        ideas (FlightAgentOutput): The travel ideas from the AI agent
        
    Returns:
        str: Formatted HTML message
    """
    logger.info("Formatting travel ideas as HTML message")
    message = "<b>🌟 Travel Ideas for Next Week 🌟</b>\n\n"
    
    for idea in ideas.ideas:
        message += f"<b>{idea.header}</b>\n"
        message += f"<i>{idea.motivation}</i>\n\n"
        message += f"{idea.destination_description}\n\n"
        
        summary = idea.travel_summary
        message += "<b>Travel Details:</b>\n"
        message += f"📍 From: {summary.starting_point}\n"
        message += f"✈️ To: {summary.destination}\n"
        message += f"📅 Dates: {summary.travel_dates}\n"
        message += f"💰 Price: {summary.flight_price}\n"
        if summary.flight_number:
            message += f"🔢 Flight: {summary.flight_number}\n"
        message += f"🔗 <a href='{summary.booking_link}'>Book Now</a>\n\n"
        message += "➖➖➖➖➖➖➖➖➖➖\n\n"
    
    logger.info("Message formatting completed")
    return message


async def main() -> None:
    """Main function to run the telegram sender."""
    try:
        logger.info("Starting telegram sender")
        
        # Initialize AI agent
        logger.info("Initializing AI agent")
        agent = AiAgent()
        
        # Get travel ideas
        logger.info("Getting travel ideas from AI agent")
        ideas = await agent.run_agent(PROMPT)
        
        # Format and send message
        logger.info("Formatting and sending message")
        message = format_travel_ideas(ideas)
        await send_to_telegram(message)
        
        logger.info("Successfully completed telegram sender execution")
        print("Successfully sent travel ideas to Telegram channel")
        
    except Exception as e:
        logger.error(f"Error in telegram sender: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 