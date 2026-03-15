# Схемы tools — telegram-mcp-plus

Формат ответов совместим с оригинальным telegram-mcp для лёгкой миграции.

---

## tg_me

**Описание:** Get current Telegram account info

**Параметры:** нет

**Ответ:**
```json
{
  "id": 123456789,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe"
}
```

---

## tg_dialogs

**Описание:** Get list of Telegram dialogs (chats, channels, users)

**Параметры:**
| Поле | Тип | Обязательное | Описание |
|------|-----|---|----------|
| only_unread | bool | нет | Include only dialogs with unread messages |
| offset | string | нет | Offset for pagination (from previous response) |

**Ответ:**
```json
{
  "dialogs": [
    {
      "name": "johndoe",
      "type": "user",
      "title": "John Doe",
      "last_message": {
        "who": "John",
        "when": "2026-03-12 22:33:30",
        "text": "Привет!",
        "is_unread": false
      }
    }
  ],
  "offset": "next-page-token"
}
```

---

## tg_dialog

**Описание:** Get messages from a specific dialog

**Параметры:**
| Поле | Тип | Обязательное | Описание |
|------|-----|---|----------|
| name | string | да | Dialog name or username |
| limit | int | нет | Number of messages (default 20, max 100) |
| offset_id | int | нет | Get messages older than this message ID |

**Ответ:**
```json
{
  "messages": [
    {
      "id": 12345,
      "who": "John",
      "when": "2026-03-12 22:33:30",
      "text": "Привет!",
      "is_edited": false
    }
  ],
  "offset_id": 12300
}
```

---

## tg_read

**Описание:** Mark dialog as read

**Параметры:**
| Поле | Тип | Обязательное | Описание |
|------|-----|---|----------|
| name | string | да | Dialog name or username |

**Ответ:**
```json
{
  "status": "ok",
  "dialog": "johndoe"
}
```

---

## tg_send

**Описание:** Send a message to a dialog

**Параметры:**
| Поле | Тип | Обязательное | Описание |
|------|-----|---|----------|
| name | string | да | Dialog name or username |
| text | string | да | Message text |

**Ответ:**
```json
{
  "status": "ok",
  "message_id": 12346,
  "when": "2026-03-13 18:30:00"
}
```

---

## tg_folders

**Описание:** Get list of Telegram folders (dialog filters)

**Параметры:** нет

**Ответ:**
```json
{
  "folders": [
    {
      "id": 2,
      "title": "Работа",
      "emoji": "💼"
    },
    {
      "id": 3,
      "title": "Каналы",
      "emoji": "📢"
    }
  ]
}
```

---

## tg_folder

**Описание:** Get dialogs from a specific folder

**Параметры:**
| Поле | Тип | Обязательное | Описание |
|------|-----|---|----------|
| folder_id | int | да | Folder ID (from tg_folders) |
| only_unread | bool | нет | Include only dialogs with unread messages |
| offset | string | нет | Offset for pagination |

**Ответ:** Тот же формат, что `tg_dialogs`:
```json
{
  "dialogs": [...],
  "offset": "next-page-token"
}
```
