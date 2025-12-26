# Travel Inspiration Bot

AI-powered Telegram bot that turns real Amadeus fares into travel ideas, decorates them with AI copy, hotel suggestions, and optional city photos, and posts them to one or many channels.

## Features
- Uses Amadeus for live flight data and TravelPayouts for booking links; optional Pexels photos for each destination
- GPT-4o-mini generates multilingual copy and pricing in the currency you choose
- Single-channel sender plus multi-channel runner (sequential or parallel) driven by JSON or `CHANNELS_CONFIG`
- Docker image with cron schedule read from your `channels.json` for unattended runs
- Tests, type checking, and linting via `uv`

## Project Layout
```
.
├── README_MULTI_CHANNEL.md      # Extra multi-channel examples
├── channels.example.json        # Sample config with cron field
├── docker-entrypoint.sh         # Reads cron schedule and runs multi-channel sender
├── Dockerfile
├── ev_bot/
│   ├── ai_agent.py              # Builds travel ideas from Amadeus + AI
│   ├── run_multi_channel.py     # Wrapper to run many channels
│   ├── settings.py              # Env-driven settings
│   └── telegram_sender.py       # Single channel sender
├── rebuild                      # Helper to rebuild and restart the Docker container
└── tests/
```

## Prerequisites
- Python 3.12 (project targets 3.10–3.12)
- [`uv`](https://github.com/astral-sh/uv) installed

## Setup
1) Create your env file in the repo root (one level above `ev_bot/`):
```bash
cp .env.template .env
# fill in required keys
```
2) Install dependencies (creates `.venv` inside `ev_bot/`):
```bash
cd ev_bot
uv sync
```
3) Optional: activate the virtualenv before running commands:
```bash
source .venv/bin/activate
```
All `uv` commands below assume your shell is inside `ev_bot/`; adjust relative paths if you run them elsewhere.

## Environment variables (`.env`)
- `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET` (required)
- `TRAVELPAYOUTS_TOKEN`, `TRAVELPAYOUTS_MARKER` (required for booking links)
- `OPENAI_API_KEY` (required)
- `PEXELS_API_KEY` (optional, adds destination photos)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID` (required unless passed via CLI)

## Run a single channel
Either set env vars or pass CLI overrides:
```bash
uv run python telegram_sender.py \
  --bot-token "YOUR_BOT_TOKEN" \
  --channel-id "@your_channel" \
  --origin MAD \
  --language Spanish \
  --currency EUR \
  --amadeus-client-id "YOUR_ID" \
  --amadeus-client-secret "YOUR_SECRET"
```
Supported languages: English, Spanish, French, German, Italian, Russian. Currency is any ISO code supported by Amadeus.

## Run multiple channels
Create `channels.json` (or use `channels.example.json` as a base). The file can be an array or include a `channels` key; if you are using Docker/cron add a top-level `cron` string:
```json
{
  "cron": "0 */6 * * *",
  "channels": [
    {
      "telegram_bot_token": "TOKEN_1",
      "telegram_channel_id": "@channel_es",
      "origin": "MAD",
      "language": "Spanish",
      "currency": "EUR"
    },
    {
      "telegram_bot_token": "TOKEN_2",
      "telegram_channel_id": "@channel_en",
      "origin": "NYC",
      "language": "English",
      "currency": "USD"
    }
  ]
}
```
The commands below assume `channels.json` lives in the repo root (one level above `ev_bot/`).
Run sequentially (default) or in parallel:
```bash
uv run python run_multi_channel.py --config ../channels.json
uv run python run_multi_channel.py --config ../channels.json --parallel
```
You can also pass config via `CHANNELS_CONFIG`:
```bash
export CHANNELS_CONFIG='[{"telegram_bot_token":"TOKEN","telegram_channel_id":"@channel","origin":"MAD","language":"Spanish","currency":"EUR"}]'
uv run python run_multi_channel.py --from-env
```

See `README_MULTI_CHANNEL.md` for more configuration examples and CLI flags (`--sender-script`, per-channel API overrides, etc.).

## Docker and cron deployment
The Docker image installs dependencies with `uv`, reads `CONFIG_PATH` (default `/config/channels.json`), and configures cron using the `cron` field inside that file.
```bash
docker build -t amadeus .
docker run -d --name amadeus \
  -v $(pwd)/channels.json:/config/channels.json \
  --env-file .env \
  amadeus
```
Use `CONFIG_PATH` to point to a different config file. The `rebuild` helper mirrors the same build/run steps.

## Tests and quality checks
```bash
cd ev_bot
uv run pytest
uv run ruff check .
uv run mypy .
uv run black .
```
