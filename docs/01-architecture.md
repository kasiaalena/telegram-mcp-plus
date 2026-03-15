# Архитектура telegram-mcp-plus

## Стек технологий

- **Python 3.11+**
- **Telethon 1.42+** — MTProto клиент для Telegram API
- **MCP Python SDK (FastMCP)** — фреймворк для MCP-серверов
- **hatchling** — система сборки для PyPI

## Структура проекта

```
telegram-mcp-plus/
├── pyproject.toml              # Конфигурация пакета, зависимости, entry point
├── README.md                   # Документация
├── LICENSE                     # MIT
├── src/
│   └── telegram_mcp_plus/
│       ├── __init__.py         # Версия пакета
│       ├── __main__.py         # python -m telegram_mcp_plus
│       ├── server.py           # MCP-сервер, регистрация tools
│       ├── auth.py             # CLI-команда авторизации
│       ├── client.py           # Singleton Telethon-клиент, управление сессией
│       └── tools/
│           ├── __init__.py     # Экспорт всех tools
│           ├── me.py           # tg_me — информация об аккаунте
│           ├── dialogs.py      # tg_dialogs — список чатов
│           ├── dialog.py       # tg_dialog — сообщения из чата
│           ├── read.py         # tg_read — пометить прочитанным
│           ├── send.py         # tg_send — отправить сообщение
│           ├── folders.py      # tg_folders — список папок
│           └── folder.py       # tg_folder — диалоги конкретной папки
└── tests/
    ├── conftest.py             # Фикстуры, mock-клиент
    ├── test_me.py
    ├── test_dialogs.py
    ├── test_dialog.py
    ├── test_read.py
    ├── test_send.py
    ├── test_folders.py
    ├── test_folder.py
    ├── test_security.py
    └── test_performance.py
```

## Транспорт

- **stdio** — стандартный ввод/вывод (JSON-RPC через stdin/stdout)
- Все логи — ТОЛЬКО в stderr (иначе сломается протокол)

## Управление сессией

- Сессия Telethon хранится в SQLite-файле: `~/.telegram-mcp-plus/session.session`
- Один файл = один аккаунт
- Клиент создаётся один раз при старте сервера, переиспользуется всеми tools
- При отсутствии сессии — сервер возвращает ошибку с инструкцией запустить `telegram-mcp-plus auth`

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `TG_APP_ID` | Да | API ID из my.telegram.org |
| `TG_API_HASH` | Да | API Hash из my.telegram.org |
| `TG_SESSION_PATH` | Нет | Путь к файлу сессии (по умолчанию ~/.telegram-mcp-plus/) |

## Обработка ошибок

- **FloodWaitError** — Telethon автоматически ждёт, если < 60 секунд. Если больше — возвращаем ошибку пользователю с указанием времени ожидания.
- **Нет авторизации** — понятное сообщение: "Запустите telegram-mcp-plus auth"
- **Невалидный ввод** — валидация через Pydantic/type hints в FastMCP
- Все ошибки возвращаются как `isError: true` в MCP-формате

## Диаграмма потока данных

```
Claude Code / Claude Desktop
        │
        ▼ (JSON-RPC через stdio)
   MCP Server (FastMCP)
        │
        ▼ (вызов tool)
   Tool Handler (tools/*.py)
        │
        ▼ (async вызов)
   Telethon Client (client.py)
        │
        ▼ (MTProto)
   Telegram API
```
