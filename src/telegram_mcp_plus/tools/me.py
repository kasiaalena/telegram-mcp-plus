from telegram_mcp_plus.client import ensure_connected


async def tg_me() -> dict:
    """Get current Telegram account info."""
    try:
        client = await ensure_connected()
        me = await client.get_me()
        return {
            "id": me.id,
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "username": me.username or "",
        }
    except Exception as e:
        return {"error": str(e)}
