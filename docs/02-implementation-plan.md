# План реализации telegram-mcp-plus

## Фаза 1: Каркас проекта (30 мин)

### 1.1 Инициализация
- [ ] Создать `pyproject.toml` с зависимостями (telethon, mcp[cli])
- [ ] Создать структуру папок src/telegram_mcp_plus/
- [ ] `__init__.py` с версией `__version__ = "0.1.0"`
- [ ] `__main__.py` для запуска через `python -m`

### 1.2 Entry points
- [ ] `telegram-mcp-plus` — основная команда (запуск MCP-сервера)
- [ ] `telegram-mcp-plus auth` — авторизация в Telegram

### 1.3 Базовый сервер
- [ ] `server.py` — инициализация FastMCP, stdio transport
- [ ] Логирование в stderr
- [ ] Graceful shutdown

## Фаза 2: Клиент Telegram (30 мин)

### 2.1 client.py — Singleton Telethon-клиент
- [ ] Чтение TG_APP_ID, TG_API_HASH из env
- [ ] Определение пути сессии (~/.telegram-mcp-plus/session)
- [ ] Создание и подключение TelegramClient
- [ ] Проверка авторизации при старте
- [ ] Понятная ошибка если не авторизован

### 2.2 auth.py — CLI авторизация
- [ ] Парсинг аргументов (--phone, --password для 2FA)
- [ ] Отправка кода: client.send_code_request()
- [ ] Ввод кода из stdin
- [ ] Обработка 2FA (SessionPasswordNeededError)
- [ ] Сохранение сессии
- [ ] Вывод "Авторизация успешна!"

## Фаза 3: Базовые tools (1 час)

### 3.1 tg_me
- [ ] Вызов client.get_me()
- [ ] Возврат: id, first_name, last_name, username, phone

### 3.2 tg_dialogs
- [ ] Параметры: only_unread (bool), offset (str, опционально)
- [ ] Вызов client.iter_dialogs()
- [ ] Фильтрация по unread если запрошено
- [ ] Пагинация через offset
- [ ] Возврат: name, type (user/channel/group), title, last_message, is_unread
- [ ] Лимит: 20 диалогов на запрос

### 3.3 tg_dialog
- [ ] Параметры: name (str), limit (int, default 20), offset_id (int, опционально)
- [ ] Поиск entity по name/username
- [ ] Вызов client.iter_messages()
- [ ] Возврат: id, text, date, sender, is_edited

### 3.4 tg_read
- [ ] Параметры: name (str)
- [ ] Поиск entity
- [ ] Вызов client.send_read_acknowledge()
- [ ] Подтверждение

### 3.5 tg_send
- [ ] Параметры: name (str), text (str)
- [ ] Поиск entity
- [ ] Вызов client.send_message()
- [ ] Возврат: id отправленного сообщения, timestamp

## Фаза 4: Папки — ключевая фича (45 мин)

### 4.1 tg_folders
- [ ] Вызов client(GetDialogFiltersRequest())
- [ ] Парсинг ответа: id папки, название, иконка, количество чатов
- [ ] Возврат списка всех папок

### 4.2 tg_folder
- [ ] Параметры: folder_id (int), only_unread (bool), offset (str)
- [ ] Вызов client.iter_dialogs(folder=folder_id)
- [ ] Тот же формат что tg_dialogs, но фильтрованный по папке
- [ ] Пагинация

## Фаза 5: Упаковка и публикация (30 мин)

### 5.1 pyproject.toml
- [ ] Финализация метаданных (description, author, license, urls)
- [ ] Entry points для CLI
- [ ] Проверка: `uv build` собирает пакет

### 5.2 README.md
- [ ] Описание, установка, настройка, примеры

### 5.3 Тестовый запуск
- [ ] `uvx telegram-mcp-plus auth --phone ...` — авторизация
- [ ] Подключение к Claude Code, проверка всех tools

## Фаза 6: Тестирование (1 час)

- [ ] Unit-тесты для каждого tool
- [ ] Тесты безопасности (см. 04-security-tests.md)
- [ ] Тесты производительности (см. 05-performance-tests.md)
- [ ] Интеграционный тест: полный цикл через MCP

## Общее время: ~4 часа
