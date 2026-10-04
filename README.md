# telegram-mcp-plus

Telegram MCP server for Claude Code — read messages, send replies, and work with folders via Telegram API.

Built on [Telethon](https://github.com/LonamiWebs/Telethon).

---

## What it does

Connects your Telegram account to Claude Code so you can:
- Read messages from any chat or channel
- Send messages
- Browse and filter chats by folder
- Mark chats as read

---

## Installation

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uvx telegram-mcp-plus
```

---

## Setup

### 1. Get Telegram API credentials

Go to [my.telegram.org](https://my.telegram.org) → API development tools → create an app.

You'll get:
- `App api_id` → this is your `TG_APP_ID`
- `App api_hash` → this is your `TG_API_HASH`

### 2. Authorize your account

```bash
TG_APP_ID=your_id TG_API_HASH=your_hash telegram-mcp-plus auth --phone +79001234567
```

Enter the code from Telegram when prompted. Session is saved locally at `~/.telegram-mcp-plus/`.

### 3. Add to Claude Code config

Open `~/.claude.json` and add:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "uvx",
      "args": ["telegram-mcp-plus"],
      "env": {
        "TG_APP_ID": "your_id",
        "TG_API_HASH": "your_hash"
      }
    }
  }
}
```

Restart Claude Code — Telegram tools will appear automatically.

---

## Available tools

| Tool | Description |
|------|-------------|
| `tg_me` | Get current account info |
| `tg_dialogs` | List chats and channels |
| `tg_dialog` | Get messages from a specific chat |
| `tg_read` | Mark chat as read |
| `tg_send` | Send a message |
| `tg_folders` | List your Telegram folders |
| `tg_folder` | Get chats from a specific folder |

---

## Security

- Your credentials are stored in environment variables, never in the code
- Session files are stored locally at `~/.telegram-mcp-plus/` with restricted permissions (700)
- Never share your `TG_API_HASH` or session files

---

## License

MIT
