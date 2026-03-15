"""Security tests: credential leaks, session protection, input injection, data exposure."""

import os
import re
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from tests.conftest import make_user, make_message, make_dialog


# ── S2: Credentials protection ────────────────────────────────────

class TestCredentialsProtection:
    @pytest.mark.asyncio
    async def test_api_hash_not_in_me_response(self, patch_ensure_connected):
        """S2.2: API hash must never appear in tool responses."""
        from telegram_mcp_plus.tools.me import tg_me
        client = patch_ensure_connected
        me = make_user()
        client.get_me = AsyncMock(return_value=me)

        result = await tg_me()
        result_str = json.dumps(result)
        assert "fake_hash_for_testing" not in result_str
        assert "api_hash" not in result_str.lower()

    @pytest.mark.asyncio
    async def test_phone_not_in_me_response(self, patch_ensure_connected):
        """S4.1: tg_me must NOT return phone number."""
        from telegram_mcp_plus.tools.me import tg_me
        client = patch_ensure_connected
        me = make_user(phone="+79001234567")
        client.get_me = AsyncMock(return_value=me)

        result = await tg_me()
        result_str = json.dumps(result)
        assert "+79001234567" not in result_str
        assert "phone" not in result

    @pytest.mark.asyncio
    async def test_api_hash_not_in_dialogs_response(self, patch_ensure_connected):
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        async def mock_iter(**kw):
            yield make_dialog()
        client.iter_dialogs = mock_iter

        result = await tg_dialogs()
        result_str = json.dumps(result)
        assert "api_hash" not in result_str.lower()
        assert "auth_key" not in result_str.lower()

    @pytest.mark.asyncio
    async def test_access_hash_not_in_dialog_response(self, patch_ensure_connected):
        """S4.4: No raw Telegram metadata like access_hash."""
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        msg = make_message(id=1, text="hi")

        async def mock_iter(*a, **kw):
            yield msg
        client.iter_messages = mock_iter

        result = await tg_dialog(name="testuser")
        result_str = json.dumps(result)
        assert "access_hash" not in result_str.lower()

    def test_no_hardcoded_secrets_in_source(self):
        """S2.4: No hardcoded tokens or keys in source code."""
        import glob
        src_dir = os.path.join(os.path.dirname(__file__), "..", "src")
        secret_patterns = [
            r'\b[0-9a-f]{32}\b',  # MD5-like hashes (potential API hashes)
        ]
        # Patterns that are clearly secrets (API keys, tokens)
        danger_patterns = [
            r'api_hash\s*=\s*["\'][0-9a-f]{20,}["\']',
            r'api_id\s*=\s*\d{5,}',
            r'token\s*=\s*["\'].{20,}["\']',
        ]

        for py_file in glob.glob(os.path.join(src_dir, "**", "*.py"), recursive=True):
            with open(py_file) as f:
                content = f.read()
            for pattern in danger_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                assert not matches, f"Potential hardcoded secret in {py_file}: {matches}"


# ── S3: Input validation ──────────────────────────────────────────

class TestInputValidation:
    @pytest.mark.asyncio
    async def test_sql_injection_in_name(self, patch_ensure_connected):
        """S3.1: SQL injection attempt should result in 'Dialog not found'."""
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_dialog(name="'; DROP TABLE--")

    @pytest.mark.asyncio
    async def test_path_traversal_in_name(self, patch_ensure_connected):
        """S3.2: Path traversal attempt should result in 'Dialog not found'."""
        from telegram_mcp_plus.tools.send import tg_send
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_send(name="../../etc/passwd", text="test")

    @pytest.mark.asyncio
    async def test_xss_in_text_sent_as_plain(self, patch_ensure_connected):
        """S3.3: XSS payload should be sent as plain text."""
        from telegram_mcp_plus.tools.send import tg_send
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        sent = MagicMock()
        sent.id = 1
        sent.date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        client.send_message = AsyncMock(return_value=sent)

        xss = "<script>alert(1)</script>"
        result = await tg_send(name="testuser", text=xss)
        # Should succeed — text is passed as-is (plain text)
        assert result["status"] == "ok"
        # Verify the actual text was passed without modification
        client.send_message.assert_called_once_with(entity, xss)

    @pytest.mark.asyncio
    async def test_very_long_name(self, patch_ensure_connected):
        """S3.4: Very long name should not cause OOM, just error."""
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_dialog(name="a" * 10000)

    @pytest.mark.asyncio
    async def test_null_bytes_in_name(self, patch_ensure_connected):
        """S3.7: Null bytes should not cause unexpected behavior."""
        from telegram_mcp_plus.tools.read import tg_read
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_read(name="user\x00name")

    @pytest.mark.asyncio
    async def test_unicode_attack_in_name(self, patch_ensure_connected):
        """S3.6: Unicode tricks (RTL override, zero-width) should be handled."""
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        client.get_entity = AsyncMock(side_effect=ValueError("not found"))

        # RTL override + zero-width chars
        evil_name = "\u202e\u200b\u200ctest\u200d"
        with pytest.raises(ValueError, match="Dialog not found"):
            await tg_dialog(name=evil_name)

    @pytest.mark.asyncio
    async def test_negative_limit(self, patch_ensure_connected):
        """S3.8: Negative limit should be handled gracefully."""
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        async def mock_iter(*a, **kw):
            return
            yield
        client.iter_messages = mock_iter

        # Should not crash — min(negative, 100) = negative, but iter handles it
        result = await tg_dialog(name="testuser", limit=-1)
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_empty_text_rejected(self, patch_ensure_connected):
        """S3: Empty message text must be rejected."""
        from telegram_mcp_plus.tools.send import tg_send
        with pytest.raises(ValueError, match="empty"):
            await tg_send(name="testuser", text="")

    @pytest.mark.asyncio
    async def test_json_injection_in_offset(self, patch_ensure_connected):
        """Malformed JSON in offset should be silently ignored."""
        from telegram_mcp_plus.tools.dialogs import tg_dialogs
        client = patch_ensure_connected

        async def mock_iter(**kw):
            return
            yield
        client.iter_dialogs = mock_iter

        # Various malicious offset values
        for bad_offset in [
            '{"date": "not-a-date"}',
            '{"__proto__": {"admin": true}}',
            'a' * 10000,
        ]:
            result = await tg_dialogs(offset=bad_offset)
            assert "error" not in result


# ── S4: Data leak prevention ──────────────────────────────────────

class TestDataLeakPrevention:
    @pytest.mark.asyncio
    async def test_me_only_public_fields(self, patch_ensure_connected):
        """S4.1: tg_me should return only id, first_name, last_name, username."""
        from telegram_mcp_plus.tools.me import tg_me
        client = patch_ensure_connected
        me = make_user()
        client.get_me = AsyncMock(return_value=me)

        result = await tg_me()
        allowed_keys = {"id", "first_name", "last_name", "username"}
        assert set(result.keys()) == allowed_keys

    @pytest.mark.asyncio
    async def test_error_does_not_expose_stacktrace(self):
        """S4.3: Error responses should be user-friendly, no stack traces."""
        from telegram_mcp_plus.tools.me import tg_me
        with patch("telegram_mcp_plus.tools.me.ensure_connected",
                   side_effect=RuntimeError("Not authorized. Run: telegram-mcp-plus auth --phone <your-phone>")):
            result = await tg_me()
            error_text = result["error"]
            # Should not contain file paths or line numbers
            assert "Traceback" not in error_text
            assert ".py" not in error_text
            assert "line " not in error_text

    @pytest.mark.asyncio
    async def test_dialog_messages_no_raw_objects(self, patch_ensure_connected):
        """S4.4: Messages should not contain raw Telegram objects."""
        from telegram_mcp_plus.tools.dialog import tg_dialog
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        msg = make_message(id=1, text="hello")

        async def mock_iter(*a, **kw):
            yield msg
        client.iter_messages = mock_iter

        result = await tg_dialog(name="testuser")
        msg_data = result["messages"][0]
        # Only expected keys
        expected_keys = {"id", "who", "when", "text", "is_edited"}
        assert set(msg_data.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_send_response_minimal(self, patch_ensure_connected):
        """tg_send response should contain only status, message_id, when."""
        from telegram_mcp_plus.tools.send import tg_send
        client = patch_ensure_connected
        entity = make_user()
        client.get_entity = AsyncMock(return_value=entity)

        sent = MagicMock()
        sent.id = 1
        sent.date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        client.send_message = AsyncMock(return_value=sent)

        result = await tg_send(name="testuser", text="hello")
        expected_keys = {"status", "message_id", "when"}
        assert set(result.keys()) == expected_keys


# ── S1: Session protection ────────────────────────────────────────

class TestSessionProtection:
    def test_session_dir_has_700_permissions(self, tmp_path):
        """S1.4: Session directory must have 700 permissions."""
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
                mode = oct(session_dir.stat().st_mode)[-3:]
                assert mode == "700", f"Session dir permissions should be 700, got {mode}"

    def test_session_not_in_project_dir(self):
        """Session should be stored in home dir, not project dir."""
        from telegram_mcp_plus.client import SESSION_DIR
        project_dir = os.path.dirname(os.path.dirname(__file__))
        assert str(SESSION_DIR).startswith(str(os.path.expanduser("~")))
        assert not str(SESSION_DIR).startswith(project_dir) or "telegram-mcp-plus" in str(SESSION_DIR)

    def test_env_file_in_gitignore(self):
        """S2: .env should be in .gitignore."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                content = f.read()
            assert ".env" in content


# ── S6: Auth error handling ───────────────────────────────────────

class TestAuthErrorHandling:
    def test_invalid_env_app_id(self):
        """S6.4: Non-integer TG_APP_ID should give clear error."""
        from telegram_mcp_plus.client import _get_credentials
        with patch.dict(os.environ, {"TG_APP_ID": "abc", "TG_API_HASH": "test"}):
            with pytest.raises(RuntimeError, match="integer"):
                _get_credentials()

    def test_empty_env_vars(self):
        """S6.4: Missing env vars should give clear error."""
        from telegram_mcp_plus.client import _get_credentials
        with patch.dict(os.environ, {"TG_APP_ID": "", "TG_API_HASH": ""}):
            with pytest.raises(RuntimeError, match="required"):
                _get_credentials()

    @pytest.mark.asyncio
    async def test_expired_session(self):
        """S1.3/S6: Expired session should return user-friendly error."""
        from telegram_mcp_plus.client import ensure_connected
        mock_client = AsyncMock()
        mock_client.is_connected = MagicMock(return_value=True)
        mock_client.is_user_authorized = AsyncMock(return_value=False)

        with patch("telegram_mcp_plus.client.get_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Not authorized"):
                await ensure_connected()
