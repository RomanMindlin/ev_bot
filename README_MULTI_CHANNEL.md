# Multi-Channel Configuration Guide

This guide explains how to run the bot for multiple Telegram channels with different configurations.

## Overview

The bot now supports two modes:

1. **Single Channel Mode**: Run `telegram_sender.py` directly with command-line arguments
2. **Multi-Channel Mode**: Use `run_multi_channel.py` to execute multiple channels

## Single Channel Mode

### Using Environment Variables

```bash
# Set variables in .env file, then run:
python ev_bot/telegram_sender.py
```

### Using Command-Line Arguments

```bash
# Override specific settings
python ev_bot/telegram_sender.py \
  --origin MAD \
  --language Spanish \
  --currency EUR

# Full configuration via CLI
python ev_bot/telegram_sender.py \
  --bot-token "YOUR_BOT_TOKEN" \
  --channel-id "@your_channel" \
  --origin MAD \
  --language Spanish \
  --currency EUR \
  --amadeus-client-id "YOUR_CLIENT_ID" \
  --amadeus-client-secret "YOUR_CLIENT_SECRET" \
  --travelpayouts-token "YOUR_TOKEN" \
  --travelpayouts-marker "YOUR_MARKER" \
  --openai-key "YOUR_OPENAI_KEY"
```

### Available Arguments

**Required (if not in .env):**
- `--bot-token`: Telegram bot token
- `--channel-id`: Telegram channel ID

**Travel Settings:**
- `--origin`: Origin airport code (e.g., MAD, NYC, LON)
- `--language`: Language for messages (English, Spanish, Russian, French, German, Italian)
- `--currency`: Currency code (EUR, USD, GBP, RUB)

**API Credentials (optional overrides):**
- `--amadeus-client-id`: Amadeus API client ID
- `--amadeus-client-secret`: Amadeus API client secret
- `--amadeus-environment`: Amadeus environment (test or prod)
- `--travelpayouts-token`: TravelPayouts API token
- `--travelpayouts-marker`: TravelPayouts affiliate marker
- `--openai-key`: OpenAI API key

## Multi-Channel Mode

### Configuration File

Create a JSON file (e.g., `channels.json`) with your channel configurations:

```json
{
  "channels": [
    {
      "telegram_bot_token": "TOKEN_1",
      "telegram_channel_id": "@channel_spain",
      "origin": "MAD",
      "language": "Spanish",
      "currency": "EUR"
    },
    {
      "telegram_bot_token": "TOKEN_2",
      "telegram_channel_id": "@channel_usa",
      "origin": "NYC",
      "language": "English",
      "currency": "USD"
    },
    {
      "telegram_bot_token": "TOKEN_3",
      "telegram_channel_id": "@channel_russia",
      "origin": "MOW",
      "language": "Russian",
      "currency": "RUB"
    }
  ]
}
```

**Note**: You can also use a simple array format without the `channels` wrapper:

```json
[
  {
    "telegram_bot_token": "TOKEN_1",
    "telegram_channel_id": "@channel_1",
    "origin": "MAD",
    "language": "Spanish",
    "currency": "EUR"
  }
]
```

### Running Multi-Channel

**Sequential execution (default):**
```bash
python run_multi_channel.py --config channels.json
```

**Parallel execution (faster):**
```bash
python run_multi_channel.py --config channels.json --parallel
```

**From environment variable:**
```bash
export CHANNELS_CONFIG='[{"telegram_bot_token":"TOKEN","telegram_channel_id":"@channel","origin":"MAD","language":"Spanish","currency":"EUR"}]'
python run_multi_channel.py --from-env
```

**Custom sender script path:**
```bash
python run_multi_channel.py --config channels.json --sender-script ./custom/path/telegram_sender.py
```

## Configuration Options

### Per-Channel Configuration

Each channel configuration supports:

**Required:**
- `telegram_bot_token`: Bot token for this channel
- `telegram_channel_id`: Channel ID (e.g., `@channelname` or `-1001234567890`)
- `origin`: IATA airport code (e.g., `MAD`, `NYC`, `LON`)
- `language`: Message language (English, Spanish, Russian, French, German, Italian)
- `currency`: Currency code (EUR, USD, GBP, RUB, etc.)

**Optional (overrides .env):**
- `amadeus_client_id`: Amadeus API client ID
- `amadeus_client_secret`: Amadeus API client secret
- `amadeus_environment`: `test` or `prod`
- `travelpayouts_token`: TravelPayouts API token
- `travelpayouts_marker`: TravelPayouts affiliate marker
- `openai_key`: OpenAI API key

### Shared Configuration

API credentials that don't change per channel should be set in `.env`:

```bash
# .env
AMADEUS_CLIENT_ID_TEST=your_test_id
AMADEUS_CLIENT_SECRET_TEST=your_test_secret
TRAVELPAYOUTS_TOKEN=your_token
TRAVELPAYOUTS_MARKER=your_marker
OPENAI_API_KEY=your_openai_key
ENVIRONMENT=test
```

## Use Cases

### Use Case 1: Same Bot, Multiple Languages

Send travel ideas from Madrid to different language audiences:

```json
{
  "channels": [
    {
      "telegram_bot_token": "SAME_TOKEN",
      "telegram_channel_id": "@madrid_es",
      "origin": "MAD",
      "language": "Spanish",
      "currency": "EUR"
    },
    {
      "telegram_bot_token": "SAME_TOKEN",
      "telegram_channel_id": "@madrid_en",
      "origin": "MAD",
      "language": "English",
      "currency": "EUR"
    },
    {
      "telegram_bot_token": "SAME_TOKEN",
      "telegram_channel_id": "@madrid_fr",
      "origin": "MAD",
      "language": "French",
      "currency": "EUR"
    }
  ]
}
```

### Use Case 2: Different Cities, Different Bots

Separate channels for different cities:

```json
{
  "channels": [
    {
      "telegram_bot_token": "MADRID_BOT_TOKEN",
      "telegram_channel_id": "@madrid_travel",
      "origin": "MAD",
      "language": "Spanish",
      "currency": "EUR"
    },
    {
      "telegram_bot_token": "NYC_BOT_TOKEN",
      "telegram_channel_id": "@nyc_travel",
      "origin": "JFK",
      "language": "English",
      "currency": "USD"
    },
    {
      "telegram_bot_token": "MOSCOW_BOT_TOKEN",
      "telegram_channel_id": "@moscow_travel",
      "origin": "MOW",
      "language": "Russian",
      "currency": "RUB"
    }
  ]
}
```

### Use Case 3: Testing and Production

Run test and production channels with different API credentials:

```json
{
  "channels": [
    {
      "telegram_bot_token": "TEST_BOT_TOKEN",
      "telegram_channel_id": "@test_channel",
      "origin": "MAD",
      "language": "Spanish",
      "currency": "EUR",
      "amadeus_environment": "test"
    },
    {
      "telegram_bot_token": "PROD_BOT_TOKEN",
      "telegram_channel_id": "@prod_channel",
      "origin": "MAD",
      "language": "Spanish",
      "currency": "EUR",
      "amadeus_environment": "prod",
      "amadeus_client_id": "PROD_CLIENT_ID",
      "amadeus_client_secret": "PROD_CLIENT_SECRET"
    }
  ]
}
```

## Scheduling

### Using Cron (Linux/Mac)

Run daily at 9 AM:
```bash
0 9 * * * cd /path/to/amadeus && /path/to/python run_multi_channel.py --config channels.json
```

Run every 6 hours:
```bash
0 */6 * * * cd /path/to/amadeus && /path/to/python run_multi_channel.py --config channels.json
```

### Using systemd Timer (Linux)

Create `/etc/systemd/system/travel-bot.service`:
```ini
[Unit]
Description=Travel Ideas Bot

[Service]
Type=oneshot
WorkingDirectory=/path/to/amadeus
ExecStart=/path/to/python run_multi_channel.py --config channels.json
User=your_user
```

Create `/etc/systemd/system/travel-bot.timer`:
```ini
[Unit]
Description=Run Travel Bot Daily

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable travel-bot.timer
sudo systemctl start travel-bot.timer
```

## Troubleshooting

### No channels processed
**Error**: `No channel configurations found`
**Solution**: Check your JSON file format or environment variable

### Invalid JSON format
**Error**: `Error loading configuration: ...`
**Solution**: Validate your JSON using a JSON validator (e.g., jsonlint.com)

### Missing required parameters
**Error**: `--bot-token and --channel-id are required`
**Solution**: Ensure each channel config has `telegram_bot_token` and `telegram_channel_id`

### API credential errors
**Solution**: Check that API credentials are set in `.env` or provided in channel config

### Channel-specific failures
Check the detailed output for each channel. The runner continues processing other channels even if one fails.

## Logs

Each execution logs to:
- Console output (stdout/stderr)
- Application logs (check your logger configuration)

For debugging, run single channel mode first:
```bash
python ev_bot/telegram_sender.py --origin MAD --language Spanish --currency EUR
```
