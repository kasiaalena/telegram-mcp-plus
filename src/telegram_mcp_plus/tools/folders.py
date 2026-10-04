from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilter, DialogFilterDefault, DialogFilterChatlist

from telegram_mcp_plus.client import ensure_connected


async def tg_folders() -> dict:
    """Get list of Telegram folders (dialog filters)."""
    try:
        client = await ensure_connected()

        result = await client(GetDialogFiltersRequest())

        folders = []
        for f in result.filters:
            if isinstance(f, DialogFilterDefault):
                folders.append({
                    "id": 0,
                    "title": "All Chats",
                    "emoji": "",
                })
            elif isinstance(f, (DialogFilter, DialogFilterChatlist)):
                folders.append({
                    "id": f.id,
                    "title": f.title,
                    "emoji": f.emoticon or "",
                })

        return {"folders": folders}
    except Exception as e:
        return {"error": str(e)}
