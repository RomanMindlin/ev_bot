FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/config/channels.json

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY ev_bot/ ./ev_bot/
WORKDIR /app/ev_bot

RUN python -m pip install --upgrade --no-cache-dir pip uv \
    && uv sync --locked \
    && rm -rf /root/.cache

COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

VOLUME ["/config"]

ENTRYPOINT ["./docker-entrypoint.sh"]
