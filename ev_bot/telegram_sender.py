import asyncio
import sys
import argparse
from aiogram import Bot
from aiogram.enums import ParseMode
from ev_bot.settings import settings
from ev_bot.ai_agent import AiAgent, FlightAgentOutput
from ev_bot.logger import setup_logger


logger = setup_logger("telegram_sender")


# Translation dictionary for static text
TRANSLATIONS = {
    'english': {
        'title': 'Travel Ideas for Next Week',
        'travel_details': 'Travel Details:',
        'from': 'From:',
        'to': 'To:',
        'dates': 'Dates:',
        'flight_price': 'Flight Price:',
        'flight': 'Flight:',
        'book_flight': 'Book Flight',
        'recommended_hotel': 'Recommended Hotel:',
        'rating': 'Rating:',
        'price': 'Price:',
        'book_hotel': 'Book Hotel'
    },
    'spanish': {
        'title': 'Ideas de Viaje para la Próxima Semana',
        'travel_details': 'Detalles del Viaje:',
        'from': 'Desde:',
        'to': 'Hasta:',
        'dates': 'Fechas:',
        'flight_price': 'Precio del Vuelo:',
        'flight': 'Vuelo:',
        'book_flight': 'Reservar Vuelo',
        'recommended_hotel': 'Hotel Recomendado:',
        'rating': 'Valoración:',
        'price': 'Precio:',
        'book_hotel': 'Reservar Hotel'
    },
    'french': {
        'title': 'Idées de Voyage pour la Semaine Prochaine',
        'travel_details': 'Détails du Voyage:',
        'from': 'De:',
        'to': 'À:',
        'dates': 'Dates:',
        'flight_price': 'Prix du Vol:',
        'flight': 'Vol:',
        'book_flight': 'Réserver le Vol',
        'recommended_hotel': 'Hôtel Recommandé:',
        'rating': 'Note:',
        'price': 'Prix:',
        'book_hotel': 'Réserver l\'Hôtel'
    },
    'german': {
        'title': 'Reiseideen für die Nächste Woche',
        'travel_details': 'Reisedetails:',
        'from': 'Von:',
        'to': 'Nach:',
        'dates': 'Daten:',
        'flight_price': 'Flugpreis:',
        'flight': 'Flug:',
        'book_flight': 'Flug Buchen',
        'recommended_hotel': 'Empfohlenes Hotel:',
        'rating': 'Bewertung:',
        'price': 'Preis:',
        'book_hotel': 'Hotel Buchen'
    },
    'italian': {
        'title': 'Idee di Viaggio per la Prossima Settimana',
        'travel_details': 'Dettagli del Viaggio:',
        'from': 'Da:',
        'to': 'A:',
        'dates': 'Date:',
        'flight_price': 'Prezzo del Volo:',
        'flight': 'Volo:',
        'book_flight': 'Prenota Volo',
        'recommended_hotel': 'Hotel Consigliato:',
        'rating': 'Valutazione:',
        'price': 'Prezzo:',
        'book_hotel': 'Prenota Hotel'
    },
    'russian': {
        'title': 'Идеи Путешествий на Следующую Неделю',
        'travel_details': 'Детали Поездки:',
        'from': 'Откуда:',
        'to': 'Куда:',
        'dates': 'Даты:',
        'flight_price': 'Цена Билета:',
        'flight': 'Рейс:',
        'book_flight': 'Забронировать Билет',
        'recommended_hotel': 'Рекомендуемый Отель:',
        'rating': 'Рейтинг:',
        'price': 'Цена:',
        'book_hotel': 'Забронировать Отель'
    }
}


def get_translations(language: str = None) -> dict:
    """
    Get translations for the specified language.
    
    Args:
        language (str): Full language name (e.g., 'English', 'Spanish', 'Russian')
        
    Returns:
        dict: Translation dictionary for the language, defaults to English
    """
    lang_key = language.lower()
    return TRANSLATIONS.get(lang_key, TRANSLATIONS['english'])


def create_prompt(language: str, currency: str) -> str:
    """Create prompt for AI agent with specified language and currency."""
    return f"""Please analyze available flights and suggest three best travel ideas for the next week.
Best here means chippest, most interesting, or most unique destinations based on current flight data.
For each idea, provide:
1. A catchy header
2. Motivation for choosing this destination
3. Brief description of the destination
4. Travel details including flight price, dates, and booking link

Please provide all text in {language} language and show prices in {currency} currency.
Include currency symbols where appropriate. Don't try to translate the currency symbol, just use the symbol itself.

Format the response as a JSON object with an 'ideas' array containing three travel ideas."""


async def send_to_telegram(message: str, bot_token: str, channel_id: str) -> None:
    """
    Send a message to a Telegram channel.
    
    Args:
        message (str): The message to send
        bot_token (str): Telegram bot token
        channel_id (str): Telegram channel ID
        
    Raises:
        ValueError: If Telegram settings are not configured
    """
    if not bot_token or not channel_id:
        logger.error("Telegram settings not configured")
        raise ValueError("Telegram bot token and channel ID must be configured")
    
    logger.info(f"Sending message to Telegram channel {channel_id}")
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Message sent successfully to {channel_id}")
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise
    finally:
        await bot.session.close()


def format_travel_ideas(ideas: FlightAgentOutput, language: str) -> str:
    """
    Format travel ideas as an HTML message with translations.
    
    Args:
        ideas (FlightAgentOutput): The travel ideas from the AI agent
        language (str): Target language for formatting
        
    Returns:
        str: Formatted HTML message in the target language
    """
    logger.info(f"Formatting travel ideas as HTML message in {language}")
    t = get_translations(language)
    
    message = f"<b>🌟 {t['title']} 🌟</b>\n\n"
    
    for idea in ideas.ideas:
        message += f"<b>{idea.header}</b>\n"
        message += f"<i>{idea.motivation}</i>\n\n"
        message += f"{idea.destination_description}\n\n"
        
        summary = idea.travel_summary
        message += f"<b>{t['travel_details']}</b>\n"
        message += f"📍 {t['from']} {summary.starting_point}\n"
        message += f"✈️ {t['to']} {summary.destination}\n"
        message += f"📅 {t['dates']} {summary.travel_dates_str}\n"
        message += f"💰 {t['flight_price']} {summary.flight_price}\n"
        if summary.flight_number:
            message += f"🔢 {t['flight']} {summary.flight_number}\n"
        message += f"🔗 <a href='{summary.booking_link}'>{t['book_flight']}</a>\n\n"
        
        if summary.hotel:
            message += f"<b>🏨 {t['recommended_hotel']}</b>\n"
            message += f"📌 {summary.hotel.name}\n"
            message += f"⭐️ {t['rating']} {summary.hotel.rating}\n"
            message += f"💰 {t['price']} {summary.hotel.price}\n"
            # message += f"🔗 <a href='{summary.hotel.booking_link}'>{t['book_hotel']}</a>\n"
        
        message += "\n➖➖➖➖➖➖➖➖➖➖\n\n"
    
    logger.info("Message formatting completed")
    return message


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Send travel ideas to Telegram channel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Use environment variables
  python telegram_sender.py
  
  # Override with command line arguments
  python telegram_sender.py --origin MAD --language Spanish --currency EUR
  
  # Full configuration via CLI
  python telegram_sender.py \
    --bot-token YOUR_TOKEN \
    --channel-id @your_channel \
    --origin MAD \
    --language Spanish \
    --currency EUR \
    --amadeus-client-id YOUR_ID \
    --amadeus-client-secret YOUR_SECRET
        """
    )
    
    # Telegram settings
    parser.add_argument('--bot-token', help='Telegram bot token')
    parser.add_argument('--channel-id', help='Telegram channel ID')
    
    # Travel settings
    parser.add_argument('--origin', help='Origin airport code (e.g., MAD, NYC)')
    parser.add_argument('--language', help='Language for messages (e.g., English, Spanish, Russian)')
    parser.add_argument('--currency', help='Currency code (e.g., EUR, USD)')
    
    # API credentials (optional overrides)
    parser.add_argument('--amadeus-client-id', help='Amadeus API client ID')
    parser.add_argument('--amadeus-client-secret', help='Amadeus API client secret')
    parser.add_argument('--travelpayouts-token', help='TravelPayouts API token')
    parser.add_argument('--travelpayouts-marker', help='TravelPayouts affiliate marker')
    parser.add_argument('--openai-key', help='OpenAI API key')
    
    return parser.parse_args()


async def main() -> None:
    """Main function to run the telegram sender."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Use CLI args with fallback to environment variables
        bot_token = args.bot_token or settings.telegram_bot_token
        channel_id = args.channel_id or settings.telegram_channel_id
        origin = args.origin or settings.origin
        language = args.language or settings.language or 'English'
        currency = args.currency or settings.currency
        
        # Override settings if provided via CLI
        if args.amadeus_client_id:
            settings.test_client_id = args.amadeus_client_id
        if args.amadeus_client_secret:
            settings.test_client_secret = args.amadeus_client_secret
        if args.travelpayouts_token:
            settings.travelpayouts_token = args.travelpayouts_token
        if args.travelpayouts_marker:
            settings.travelpayouts_marker = args.travelpayouts_marker
        if args.openai_key:
            settings.openai_key = args.openai_key
        
        # Override origin and currency for this run
        settings.origin = origin
        settings.currency = currency
        
        logger.info(f"Starting telegram sender - Origin: {origin}, Language: {language}, Currency: {currency}")
        
        # Validate required settings
        if not bot_token or not channel_id:
            logger.error("Missing required Telegram settings")
            print("Error: --bot-token and --channel-id are required (or set via environment)", file=sys.stderr)
            sys.exit(1)
        
        # Initialize AI agent
        logger.info("Initializing AI agent")
        agent = AiAgent()
        
        # Create prompt with specified language and currency
        prompt = create_prompt(language, currency)
        
        # Get travel ideas
        logger.info(f"Getting travel ideas from {origin}")
        ideas = await agent.run_agent(prompt)
        
        # Format and send message
        logger.info(f"Formatting message in {language}")
        message = format_travel_ideas(ideas, language)
        
        await send_to_telegram(message, bot_token, channel_id)
        
        logger.info("Successfully completed telegram sender execution")
        print(f"Successfully sent travel ideas to Telegram channel {channel_id}")
        
    except Exception as e:
        logger.error(f"Error in telegram sender: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 