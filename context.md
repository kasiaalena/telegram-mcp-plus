# telegram-mcp-plus — контекст проекта

## Что это
Собственный MCP-сервер для Telegram, построен на Telethon. Позволяет Claude читать чаты, отправлять сообщения и работать с папками Telegram.

## Структура проекта

```
tg-mcp-plus/
├── src/telegram_mcp_plus/   — исходный код сервера
├── run_mcp.sh               — скрипт запуска (загружает .env, выставляет PYTHONPATH)
├── .env                     — креды Telegram (TG_APP_ID, TG_API_HASH)
├── .venv/                   — виртуальное окружение (uv)
├── pyproject.toml
└── uv.lock
```

## Как запускается

Скрипт `run_mcp.sh`:
```bash
#!/bin/bash
cd /Users/kasiaalena/Documents/Claude/tg-mcp-plus
source .env
export TG_APP_ID TG_API_HASH
export PYTHONPATH=src
exec .venv/bin/python -m telegram_mcp_plus
```

Креды Telegram загружаются из `.env`, а не из переменных окружения shell.

## Где подключён

### 1. Файл проекта `.mcp.json`
Путь: `/Users/kasiaalena/Documents/Claude/.mcp.json`
```json
{
  "mcpServers": {
    "telegram": {
      "command": "bash",
      "args": ["/Users/kasiaalena/Documents/Claude/tg-mcp-plus/run_mcp.sh"]
    }
  }
}
```

### 2. Глобальный конфиг `~/.claude.json`
В секции `projects` прописан для двух путей:
- `/Users/kasiaalena/Documents/Claude`
- `/Users/kasiaalena`

Оба указывают на тот же `run_mcp.sh`.

## Сессия Telegram
Файл: `~/.telegram-mcp-plus/session.session` — уже авторизован, повторная авторизация не нужна.

## Разрешения
В `~/.claude/settings.local.json` разрешены инструменты:
- `mcp__telegram__tg_folders`
- `mcp__telegram__tg_folder`
- `mcp__telegram__tg_dialogs`
- `mcp__telegram__tg_dialog`

## Доступные инструменты

| Инструмент | Что делает |
|------------|------------|
| `tg_me` | Информация об аккаунте |
| `tg_dialogs` | Список чатов и каналов |
| `tg_dialog` | Сообщения из конкретного чата |
| `tg_read` | Отметить чат как прочитанный |
| `tg_send` | Отправить сообщение |
| `tg_folders` | Список папок |
| `tg_folder` | Чаты из конкретной папки |

## Тесты

Тестовая инфраструктура настроена: pytest + pytest-asyncio.

Запуск:
```bash
cd /Users/kasiaalena/Documents/Claude/tg-mcp-plus
uv run pytest tests/ -v
```

Два файла тестов, 64 теста, все проходят:

- **test_stability.py** (40 тестов) — работа каждого tool (успех, ошибки, пустые данные), обработка потери соединения, валидация параметров, helper-функции, клиентский модуль (креды, сессия, переподключение)
- **test_security.py** (24 теста) — защита credentials (API hash, телефон не утекают), input validation (SQL injection, path traversal, XSS, null bytes, unicode-атаки, JSON injection), data leak prevention (только публичные поля, нет stack trace в ошибках), защита сессии (права 700, .env в .gitignore)

Все тесты работают на моках, Telegram-аккаунт не нужен.

## Исправления после тестирования (2026-03-15)

| Файл | Что исправлено |
|------|---------------|
| `tools/dialog.py` | Добавлен try/except (раньше падал при потере соединения); limit теперь от 1 до 100 (раньше мог быть отрицательным) |
| `tools/read.py` | Добавлен try/except (раньше падал при потере соединения) |
| `tools/send.py` | Добавлен try/except; добавлен лимит длины сообщения 4096 символов |

## Известные особенности
- Python 3.14 не подхватывает `.pth` файлы — обходится через `PYTHONPATH=src` в `run_mcp.sh`
- При изменении конфига нужно выполнить "Claude: Restart MCP Servers" или перезапустить VS Code
