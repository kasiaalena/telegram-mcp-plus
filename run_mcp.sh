#!/bin/bash
cd "$(dirname "$0")"
source .env
export TG_APP_ID TG_API_HASH
export PYTHONPATH=src
exec .venv/bin/python -m telegram_mcp_plus
