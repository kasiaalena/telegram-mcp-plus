from telegram_mcp_plus.client import ensure_connected


async def _resolve_entity(client, name: str):
    try:
        return await client.get_entity(name)
    except (ValueError, TypeError):
        raise ValueError(f"Dialog not found: {name}")


async def tg_read(name: str) -> dict:
    """Mark a dialog as read."""
    try:
        client = await ensure_connected()

        entity = await _resolve_entity(client, name)
        await client.send_read_acknowledge(entity)

        return {"status": "ok", "dialog": name}
    except ValueError:
        raise
    except Exception as e:
        return {"error": str(e)}
