"""Stability tests: error handling, edge cases, input validation."""

import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone

from tests.conftest import make_user, make_message, make_dialog


# ── tg_me ──────────────────────────────────────────────────────────

class TestTgMe:
    @pytest.mark.asyncio
    async def test_success(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.me import tg_me
        client = patch_ensure_connected
        me = make_user(id=42, first_name="Alice", last_name="Smith", username="alice")
        client.get_me = AsyncMock(return_value=me)

        result = await tg_me()
        assert result["id"] == 42
        assert result["first_name"] == "Alice"
        assert result["last_name"] == "Smith"
        assert result["username"] == "alice"

    @pytest.mark.asyncio
    async def test_not_authorized(self):
        """When session is missing, should return error."""
        from telegram_mcp_plus.tools.me import tg_me
        with patch("telegram_mcp_plus.tools.me.ensure_connected",
                   side_effect=RuntimeError("Not authorized. Run: telegram-mcp-plus auth --phone <your-phone>")):
            result = await tg_me()
            assert "error" in result
            assert "Not authorized" in result["error"]

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Network failure should return error, not crash."""
        from telegram_mcp_plus.tools.me import tg_me
        with patch("telegram_mcp_plus.tools.me.ensure_connected",
                   side_effect=ConnectionError("Connection lost")):
            result = await tg_me()
            assert "error" in result

    @pytest.mark.asyncio
    async def test_no_phone_in_response(self, patch_ensure_connected):
        """tg_me should NOT return phone number."""
        from telegram_mcp_plus.tools.me import tg_me
        client = patch_ensure_connected
        me = make_user(phone="+79001234567")
        client.get_me = AsyncMock(return_value=me)

        result = await tg_me()
        assert "phone" not in result


# ── tg_dialog ──────────────────────────────────────────────────────

class TestTgDialog:
    @pytest.mark.asyncio
    async def test_success(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        msgs = [make_message(id=i, text=f"msg {i}") for i in range(3)]

        async def mock_iter(*a, **kw):
            for m in msgs:
                yield m
        client.iter_messages = mock_iter

        result = await tg_dialog(name="testuser")
        assert len(result["messages"]) == 3

    @pytest.mark.asyncio
    async def test_nonexistent_chat(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_dialog(name="nonexistent_xyz")

    @pytest.mark.asyncio
    async def test_limit_capped_at_100(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        called_with = {}

        async def mock_iter(*a, **kw):
            called_with.update(kw)
            return
            yield  # make it an async generator
        client.iter_messages = mock_iter

        await tg_dialog(name="testuser", limit=500)
        assert called_with["limit"] == 100

    @pytest.mark.asyncio
    async def test_negative_limit_becomes_1(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        called_with = {}

        async def mock_iter(*a, **kw):
            called_with.update(kw)
            return
            yield
        client.iter_messages = mock_iter

        await tg_dialog(name="testuser", limit=-1)
        assert called_with["limit"] == 1

    @pytest.mark.asyncio
    async def test_connection_error_returns_error(self):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        with patch("telegram_mcp_plus.tools.dialog.ensure_connected",
                   side_effect=ConnectionError("Network down")):
            result = await tg_dialog(name="test")
            assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_chat(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        async def mock_iter(*a, **kw):
            return
            yield
        client.iter_messages = mock_iter

        result = await tg_dialog(name="testuser")
        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_media_message(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        msg = make_message(id=1, text=None)

        async def mock_iter(*a, **kw):
            yield msg
        client.iter_messages = mock_iter

        result = await tg_dialog(name="testuser")
        assert result["messages"][0]["text"] == "[Media]"


# ── tg_send ────────────────────────────────────────────────────────

class TestTgSend:
    @pytest.mark.asyncio
    async def test_success(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.send import tg_send
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        sent = MagicMock()
        sent.id = 99
        sent.date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        client.send_message = AsyncMock(return_value=sent)

        result = await tg_send(name="testuser", text="Hello!")
        assert result["status"] == "ok"
        assert result["message_id"] == 99

    @pytest.mark.asyncio
    async def test_empty_text_rejected(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.send import tg_send
        with pytest.raises(ValueError, match="empty"):
            await tg_send(name="testuser", text="")

    @pytest.mark.asyncio
    async def test_whitespace_only_rejected(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.send import tg_send
        with pytest.raises(ValueError, match="empty"):
            await tg_send(name="testuser", text="   ")

    @pytest.mark.asyncio
    async def test_nonexistent_recipient(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.send import tg_send
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_send(name="nonexistent", text="hi")

    @pytest.mark.asyncio
    async def test_too_long_text_rejected(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.send import tg_send
        with pytest.raises(ValueError, match="too long"):
            await tg_send(name="testuser", text="a" * 5000)

    @pytest.mark.asyncio
    async def test_connection_error_returns_error(self):
        from telegram_mcp_plus.tools.send import tg_send
        with patch("telegram_mcp_plus.tools.send.ensure_connected",
                   side_effect=ConnectionError("Network down")):
            result = await tg_send(name="test", text="hi")
            assert "error" in result


# ── tg_read ────────────────────────────────────────────────────────

class TestTgRead:
    @pytest.mark.asyncio
    async def test_success(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.read import tg_read
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)
        client.send_read_acknowledge = AsyncMock()

        result = await tg_read(name="testuser")
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_nonexistent_chat(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.read import tg_read
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_read(name="nonexistent")

    @pytest.mark.asyncio
    async def test_connection_error_returns_error(self):
        from telegram_mcp_plus.tools.read import tg_read
        with patch("telegram_mcp_plus.tools.read.ensure_connected",
                   side_effect=ConnectionError("Network down")):
            result = await tg_read(name="test")
            assert "error" in result


# ── tg_dialogs ─────────────────────────────────────────────────────

class TestTgDialogs:
    @pytest.mark.asyncio
    async def test_success(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        dialogs = [make_dialog(name="Chat1"), make_dialog(name="Chat2")]

        async def mock_iter(**kw):
            for d in dialogs:
                yield d
        client.iter_dialogs = mock_iter

        result = await tg_dialogs()
        assert len(result["dialogs"]) == 2

    @pytest.mark.asyncio
    async def test_only_unread(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        dialogs = [
            make_dialog(name="Read", unread_count=0),
            make_dialog(name="Unread", unread_count=5),
        ]

        async def mock_iter(**kw):
            for d in dialogs:
                yield d
        client.iter_dialogs = mock_iter

        result = await tg_dialogs(only_unread=True)
        assert len(result["dialogs"]) == 1

    @pytest.mark.asyncio
    async def test_empty_list(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        async def mock_iter(**kw):
            return
            yield
        client.iter_dialogs = mock_iter

        result = await tg_dialogs()
        assert result["dialogs"] == []

    @pytest.mark.asyncio
    async def test_long_message_truncated(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        long_text = "x" * 500
        msg = make_message(text=long_text)
        dialogs = [make_dialog(name="Chat", message=msg)]

        async def mock_iter(**kw):
            for d in dialogs:
                yield d
        client.iter_dialogs = mock_iter

        result = await tg_dialogs()
        last_msg_text = result["dialogs"][0]["last_message"]["text"]
        assert len(last_msg_text) <= 203  # 200 + "..."
        assert last_msg_text.endswith("...")

    @pytest.mark.asyncio
    async def test_invalid_offset_ignored(self, patch_ensure_connected):
        """Bad offset JSON should be silently ignored, not crash."""
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        async def mock_iter(**kw):
            return
            yield
        client.iter_dialogs = mock_iter

        result = await tg_dialogs(offset="not-json")
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_connection_error_returns_error(self):
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        with patch("telegram_mcp_plus.tools.dialogs.ensure_connected",
                   side_effect=ConnectionError("Network down")):
            result = await tg_dialogs()
            assert "error" in result


# ── tg_folders ─────────────────────────────────────────────────────

class TestTgFolders:
    @pytest.mark.asyncio
    async def test_success(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.folders import tg_folders
        from telethon.tl.types import DialogFilterDefault
        client = patch_ensure_connected

        default_filter = MagicMock(spec=DialogFilterDefault)
        default_filter.__class__ = DialogFilterDefault

        result_obj = MagicMock()
        result_obj.filters = [default_filter]
        client.__call__ = AsyncMock(return_value=result_obj)
        client.return_value = result_obj

        result = await tg_folders()
        assert "folders" in result

    @pytest.mark.asyncio
    async def test_connection_error(self):
        from telegram_mcp_plus.tools.folders import tg_folders
        with patch("telegram_mcp_plus.tools.folders.ensure_connected",
                   side_effect=ConnectionError("Failed")):
            result = await tg_folders()
            assert "error" in result


# ── Client module ──────────────────────────────────────────────────

class TestClient:
    def test_missing_credentials(self):
        from telegram_mcp_plus.client import _get_credentials
        with patch.dict(os.environ, {"TG_APP_ID": "", "TG_API_HASH": ""}, clear=False):
            with pytest.raises(RuntimeError, match="required"):
                _get_credentials()

    def test_invalid_app_id(self):
        from telegram_mcp_plus.client import _get_credentials
        with patch.dict(os.environ, {"TG_APP_ID": "abc", "TG_API_HASH": "hash"}, clear=False):
            with pytest.raises(RuntimeError, match="integer"):
                _get_credentials()

    def test_valid_credentials(self):
        from telegram_mcp_plus.client import _get_credentials
        with patch.dict(os.environ, {"TG_APP_ID": "12345", "TG_API_HASH": "abcdef"}, clear=False):
            app_id, api_hash = _get_credentials()
            assert app_id == 12345
            assert api_hash == "abcdef"

    def test_session_dir_permissions(self, tmp_path):
        from telegram_mcp_plus.client import get_client
        session_dir = tmp_path / "test_session"
        with patch.dict(os.environ, {"TG_SESSION_PATH": str(session_dir)}, clear=False):
            import telegram_mcp_plus.client as client_mod
            client_mod._client = None
            try:
                get_client()
            except Exception:
                pass
            if session_dir.exists():
                perms = oct(session_dir.stat().st_mode)[-3:]
                assert perms == "700"

    @pytest.mark.asyncio
    async def test_ensure_connected_not_authorized(self):
        from telegram_mcp_plus.client import ensure_connected
        mock_client = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)
        mock_client.is_user_authorized = AsyncMock(return_value=False)

        with patch("telegram_mcp_plus.client.get_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Not authorized"):
                await ensure_connected()

    @pytest.mark.asyncio
    async def test_ensure_connected_reconnects(self):
        from telegram_mcp_plus.client import ensure_connected
        mock_client = AsyncMock()
        # is_connected is a sync method on TelegramClient
        mock_client.is_connected = MagicMock(return_value=False)
        mock_client.is_user_authorized = AsyncMock(return_value=True)

        with patch("telegram_mcp_plus.client.get_client", return_value=mock_client):
            result = await ensure_connected()
            mock_client.connect.assert_called_once()


# ── Helper functions ───────────────────────────────────────────────

class TestHelpers:
    def test_truncate_short(self):
        from telegram_mcp_plus.tools.dialogs import _truncate
        assert _truncate("hello") == "hello"

    def test_truncate_long(self):
        from telegram_mcp_plus.tools.dialogs import _truncate
        result = _truncate("a" * 300)
        assert len(result) == 203
        assert result.endswith("...")

    def test_truncate_empty(self):
        from telegram_mcp_plus.tools.dialogs import _truncate
        assert _truncate("") == ""
        assert _truncate(None) == ""

    def test_format_dt(self):
        from telegram_mcp_plus.tools.dialogs import _format_dt
        dt = datetime(2025, 3, 15, 14, 30, 0)
        assert _format_dt(dt) == "2025-03-15 14:30:00"

    def test_format_dt_none(self):
        from telegram_mcp_plus.tools.dialogs import _format_dt
        assert _format_dt(None) == ""

    def test_entity_type_user(self):
        from telegram_mcp_plus.tools.dialogs import _entity_type
        user = make_user()
        assert _entity_type(user) == "user"
