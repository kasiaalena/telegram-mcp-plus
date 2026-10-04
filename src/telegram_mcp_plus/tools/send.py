from telegram_mcp_plus.client import ensure_connected


async def _resolve_entity(client, name: str):
    try:
        return await client.get_entity(name)
    except (ValueError, TypeError):
        raise ValueError(f"Dialog not found: {name}")


MAX_TEXT_LENGTH = 4096


async def tg_send(name: str, text: str) -> dict:
    """Send a message to a dialog."""
    if not text.strip():
        raise ValueError("Message text cannot be empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Message too long: {len(text)} chars (max {MAX_TEXT_LENGTH})")

    try:
        client = await ensure_connected()

        entity = await _resolve_entity(client, name)
        result = await client.send_message(entity, text)

        return {
            "status": "ok",
            "message_id": result.id,
            "when": result.date.strftime("%Y-%m-%d %H:%M:%S"),
        }
    except ValueError:
        raise
    except Exception as e:
        return {"error": str(e)}
