import os
import sys
import logging
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import SQLiteSession

logger = logging.getLogger(__name__)

_client: TelegramClient | None = None

SESSION_DIR = Path.home() / ".telegram-mcp-plus"
SESSION_NAME = "session"


def _get_credentials() -> tuple[int, str]:
    app_id = os.environ.get("TG_APP_ID")
    api_hash = os.environ.get("TG_API_HASH")
    if not app_id or not api_hash:
        raise RuntimeError(
            "TG_APP_ID and TG_API_HASH environment variables are required. "
            "Get them at https://my.telegram.org"
        )
    try:
        return int(app_id), api_hash
    except ValueError:
        raise RuntimeError(f"TG_APP_ID must be an integer, got: {app_id!r}")


def _get_session_path() -> Path:
    custom = os.environ.get("TG_SESSION_PATH")
    if custom:
        return Path(custom)
    return SESSION_DIR


def get_client() -> TelegramClient:
    global _client
    if _client is not None:
        return _client

    app_id, api_hash = _get_credentials()
    session_dir = _get_session_path()
    session_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(session_dir, 0o700)

    session_path = str(session_dir / SESSION_NAME)
    _client = TelegramClient(session_path, app_id, api_hash)
    return _client


async def ensure_connected() -> TelegramClient:
    client = get_client()
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "Not authorized. Run: telegram-mcp-plus auth --phone <your-phone>"
        )
    return client
