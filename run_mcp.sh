#!/bin/bash
cd /Users/kasiaalena/Documents/Claude/tg-mcp-plus
source .env
export TG_APP_ID TG_API_HASH
export PYTHONPATH=src
exec .venv/bin/python -m telegram_mcp_plus
