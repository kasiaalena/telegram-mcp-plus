import sys
import asyncio
import logging

from mcp.server.fastmcp import FastMCP

from telegram_mcp_plus.tools.me import tg_me
from telegram_mcp_plus.tools.dialogs import tg_dialogs
from telegram_mcp_plus.tools.dialog import tg_dialog
from telegram_mcp_plus.tools.read import tg_read
from telegram_mcp_plus.tools.send import tg_send
from telegram_mcp_plus.tools.folders import tg_folders
from telegram_mcp_plus.tools.folder import tg_folder

# Configure logging to stderr only (stdout is reserved for JSON-RPC)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)

mcp = FastMCP("telegram-mcp-plus")

# Register all tools
mcp.tool()(tg_me)
mcp.tool()(tg_dialogs)
mcp.tool()(tg_dialog)
mcp.tool()(tg_read)
mcp.tool()(tg_send)
mcp.tool()(tg_folders)
mcp.tool()(tg_folder)


def main():
    # Check if "auth" subcommand was passed — delegate to auth module
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        sys.argv = sys.argv[1:]  # Remove the first arg so argparse works
        from telegram_mcp_plus.auth import main as auth_main
        auth_main()
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
