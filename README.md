# Travel Inspiration Bot

An AI-powered travel inspiration bot that automatically generates and sends travel ideas to a Telegram channel. The bot uses the Amadeus API to find real flight prices and combines them with AI-generated travel suggestions.

## Features

- 🤖 AI-powered travel inspiration generation
- ✈️ Real-time flight price data from Amadeus API
- 📱 Automatic posting to Telegram channel
- 🔄 Weekly automated updates
- 🎯 Personalized travel suggestions based on current trends

## Project Structure

```
.
├── ev_bot/
│   ├── __init__.py
│   ├── ai_agent.py         # AI agent for generating travel ideas
│   ├── amadeus_client.py   # Amadeus API client
│   ├── logger.py          # Logging configuration
│   ├── settings.py        # Project settings and configuration
│   └── telegram_sender.py # Telegram message sender
├── tests/
│   ├── __init__.py
│   ├── test_ai_agent.py
│   ├── test_telegram_sender.py
│   └── conftest.py
├── pyproject.toml
└── README.md
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/kgbplus/ev_bot.git
   cd ev_bot
   ```

2. Install dependencies:
   ```bash
   uv pip install -e .
   ```

3. Configure environment variables:
   ```bash
   # OpenAI API
   OPENAI_API_KEY=your_openai_api_key

   # Amadeus API
   AMADEUS_CLIENT_ID=your_amadeus_client_id
   AMADEUS_CLIENT_SECRET=your_amadeus_client_secret

   # Telegram
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHANNEL_ID=your_telegram_channel_id
   ```

## Usage

### Running the Telegram Sender

The main functionality is provided by the `telegram_sender.py` script, which:
1. Generates travel ideas using the AI agent
2. Formats them into a beautiful HTML message
3. Sends them to your Telegram channel

To run the sender:
```bash
python -m ev_bot.telegram_sender
```

### Message Format

The bot sends messages in the following format:
```
🌟 Travel Ideas for Next Week 🌟

<b>London Adventure</b>
<i>Perfect for history lovers</i>

Explore the rich history of London...

<b>Flight Details:</b>
• From: NYC
• To: LON
• Price: $500
• Dates: 2024-06-01 to 2024-06-08

<a href="https://test.com">Book Now</a>
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking
- ruff for linting

Run all checks:
```bash
ruff check .
black .
isort .
mypy .
```

## License

MIT License - see LICENSE file for details 