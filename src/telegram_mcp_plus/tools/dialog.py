from telegram_mcp_plus.client import ensure_connected


async def _resolve_entity(client, name: str):
    try:
        return await client.get_entity(name)
    except (ValueError, TypeError):
        raise ValueError(f"Dialog not found: {name}")


async def tg_dialog(name: str, limit: int = 20, offset_id: int = 0) -> dict:
    """Get messages from a specific dialog."""
    try:
        client = await ensure_connected()

        limit = max(1, min(limit, 100))
        entity = await _resolve_entity(client, name)

        messages = []
        last_id = None
        async for message in client.iter_messages(entity, limit=limit, offset_id=offset_id or 0):
            sender = await message.get_sender()
            first_name = sender.first_name if sender and hasattr(sender, "first_name") and sender.first_name else "Unknown"
            messages.append({
                "id": message.id,
                "who": first_name,
                "when": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                "text": message.text if message.text else "[Media]",
                "is_edited": message.edit_date is not None,
            })
            last_id = message.id

        return {
            "messages": messages,
            "offset_id": last_id,
        }
    except ValueError:
        raise
    except Exception as e:
        return {"error": str(e)}
