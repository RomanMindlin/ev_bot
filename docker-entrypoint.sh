#!/bin/sh

# Configure and start cron based on the schedule inside channels.json.
set -eu

CONFIG_PATH=${CONFIG_PATH:-/config/channels.json}
VENV_PATH=${VENV_PATH:-/app/ev_bot/.venv}
PYTHON_BIN=${PYTHON_BIN:-${VENV_PATH}/bin/python}
CRON_FILE=/etc/cron.d/ev-bot
LOG_TARGET=${CRON_LOG_TARGET:-/proc/1/fd/1}

if [ ! -f "${CONFIG_PATH}" ]; then
    echo "Configuration file not found at ${CONFIG_PATH}" >&2
    exit 1
fi

CRON_SCHEDULE=$("${PYTHON_BIN}" - <<'PY' "${CONFIG_PATH}"
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
try:
    data = json.loads(config_path.read_text())
except Exception as exc:
    print(f"Failed to read {config_path}: {exc}", file=sys.stderr)
    sys.exit(1)

cron_value = data.get("cron")
if not isinstance(cron_value, str) or not cron_value.strip():
    print('Missing or empty "cron" string in config', file=sys.stderr)
    sys.exit(1)

print(cron_value.strip())
PY
)

echo "Using cron schedule: ${CRON_SCHEDULE}"

COMMAND="cd /app && \
PYTHONPATH=/app \
CONFIG_PATH=\"${CONFIG_PATH}\" \
OPENAI_API_KEY=\"${OPENAI_API_KEY:-}\" \
AMADEUS_CLIENT_ID=\"${AMADEUS_CLIENT_ID:-}\" \
AMADEUS_CLIENT_SECRET=\"${AMADEUS_CLIENT_SECRET:-}\" \
TRAVELPAYOUTS_TOKEN=\"${TRAVELPAYOUTS_TOKEN:-}\" \
TRAVELPAYOUTS_MARKER=\"${TRAVELPAYOUTS_MARKER:-}\" \
${PYTHON_BIN} /app/ev_bot/run_multi_channel.py --config \"${CONFIG_PATH}\" >> ${LOG_TARGET} 2>&1"

cat > "${CRON_FILE}" <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
PYTHONPATH=/app

${CRON_SCHEDULE} root ${COMMAND}
EOF

chmod 0644 "${CRON_FILE}"

echo "Cron configured. Starting daemon..."
exec cron -f
