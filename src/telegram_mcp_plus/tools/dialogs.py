import json
from datetime import datetime, timezone
from typing import Optional

from telethon.tl.types import User, Channel, Chat

from telegram_mcp_plus.client import ensure_connected


def _entity_type(entity) -> str:
    if isinstance(entity, User):
        return "user"
    if isinstance(entity, Channel):
        return "supergroup" if entity.megagroup else "channel"
    if isinstance(entity, Chat):
        return "group"
    return "unknown"


def _truncate(text: str, max_len: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _format_dt(dt: datetime) -> str:
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _get_sender_name(message) -> str:
    if message is None:
        return ""
    sender = message.sender
    if sender is None:
        return ""
    if isinstance(sender, User):
        parts = [sender.first_name or "", sender.last_name or ""]
        name = " ".join(p for p in parts if p)
        return name or sender.username or ""
    if isinstance(sender, (Channel, Chat)):
        return sender.title or ""
    return ""


async def tg_dialogs(only_unread: bool = False, offset: Optional[str] = None) -> dict:
    """List Telegram dialogs."""
    try:
        client = await ensure_connected()

        kwargs = {"limit": 20}

        if offset:
            try:
                offset_data = json.loads(offset)
                offset_date = datetime.fromisoformat(offset_data["date"])
                kwargs["offset_date"] = offset_date
                offset_id = offset_data.get("id")
                if offset_id:
                    kwargs["offset_id"] = int(offset_id)
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        dialogs = []
        last_dialog = None

        async for dialog in client.iter_dialogs(**kwargs):
            if only_unread and dialog.unread_count <= 0:
                continue

            entity = dialog.entity
            username = ""
            if isinstance(entity, User):
                username = entity.username or ""
            elif isinstance(entity, Channel):
                username = entity.username or ""

            message = dialog.message
            last_message = None
            if message:
                last_message = {
                    "who": _get_sender_name(message),
                    "when": _format_dt(message.date),
                    "text": _truncate(message.text or ""),
                    "is_unread": dialog.unread_count > 0,
                }

            dialogs.append({
                "name": username or dialog.name or "",
                "type": _entity_type(entity),
                "title": dialog.title or dialog.name or "",
                "last_message": last_message,
            })

            last_dialog = dialog

        next_offset = None
        if last_dialog and last_dialog.message:
            next_offset = json.dumps({
                "date": last_dialog.message.date.isoformat(),
                "id": last_dialog.message.id,
            })

        return {
            "dialogs": dialogs,
            "offset": next_offset,
        }
    except Exception as e:
        return {"error": str(e)}
