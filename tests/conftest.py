import os
import sys
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Set dummy env vars so client module doesn't crash on import
os.environ.setdefault("TG_APP_ID", "12345")
os.environ.setdefault("TG_API_HASH", "fake_hash_for_testing")


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """Reset the global _client singleton before each test."""
    import telegram_mcp_plus.client as client_mod
    original = client_mod._client
    client_mod._client = None
    yield
    client_mod._client = original


@pytest.fixture
def mock_client():
    """Create a mocked TelegramClient."""
    client = AsyncMock()
    client.is_connected.return_value = True
    client.is_user_authorized = AsyncMock(return_value=True)
    return client


@pytest.fixture
def patch_ensure_connected(mock_client):
    """Patch ensure_connected to return a mock client."""
    with patch("telegram_mcp_plus.client.ensure_connected", return_value=mock_client) as p:
        # Also patch in each tool module
        with patch("telegram_mcp_plus.tools.me.ensure_connected", return_value=mock_client), \
             patch("telegram_mcp_plus.tools.dialogs.ensure_connected", return_value=mock_client), \
             patch("telegram_mcp_plus.tools.dialog.ensure_connected", return_value=mock_client), \
             patch("telegram_mcp_plus.tools.read.ensure_connected", return_value=mock_client), \
             patch("telegram_mcp_plus.tools.send.ensure_connected", return_value=mock_client), \
             patch("telegram_mcp_plus.tools.folders.ensure_connected", return_value=mock_client), \
             patch("telegram_mcp_plus.tools.folder.ensure_connected", return_value=mock_client):
            yield mock_client


def make_user(id=1, first_name="Test", last_name="User", username="testuser", phone="+79001234567"):
    """Create a mock User object."""
    from telethon.tl.types import User
    user = MagicMock(spec=User)
    user.id = id
    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    user.phone = phone
    # Make isinstance checks work
    user.__class__ = User
    return user


def make_message(id=1, text="Hello", sender=None, date=None, edit_date=None):
    """Create a mock Message."""
    msg = MagicMock()
    msg.id = id
    msg.text = text
    msg.date = date or datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    msg.edit_date = edit_date
    msg.sender = sender or make_user()
    msg.get_sender = AsyncMock(return_value=msg.sender)
    return msg


def make_dialog(name="Test Chat", title="Test Chat", unread_count=0, entity=None, message=None):
    """Create a mock Dialog."""
    dialog = MagicMock()
    dialog.name = name
    dialog.title = title
    dialog.unread_count = unread_count
    dialog.entity = entity or make_user()
    dialog.message = message or make_message()
    return dialog
