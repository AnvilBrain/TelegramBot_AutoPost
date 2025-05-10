# TelegramBot_AutoPost

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)  
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)]()

Бот для автоматического постинга в ваш Telegram-канал с надёжной памятью в JSON.

---

## 📋 Возможности

- 🕒 **Автопостинг по расписанию**  
  Проверка очереди каждые `POST_EVERY_SEC` секунд и публикация всех готовых постов.

- 💾 **Память в JSON**  
  Отложенные публикации сохраняются в файле `posts.json` и переживают перезапуск бота.

- 📷 **Текст и медиа**  
  Поддерживается отправка сообщений с картинкой (через `file_id`) или без неё.

- 🚫 **Отмена постов**  
  Команда **«Отменить посты»** выводит список запланированных публикаций с кнопками ❌ для удаления.

- 🔒 **Безопасность**  
  Бот реагирует только на владельца (по `OWNER_ID`).

---

## 📥 Установка

1. **Клонирование репозитория**  
   ```bash
   git clone https://github.com/<ВАШ_ЛОГИН>/TelegramBot_AutoPost.git
   cd TelegramBot_AutoPost

2. **Создание виртуального окружения** (рекомендуется)
   python3 -m venv venv
  source venv/bin/activate    # macOS/Linux
  venv\Scripts\activate       # Windows

3. **Установка зависимостей**
  pip install -r requirements.txt

---

## ⚙️ Конфигурация

Все ключевые параметры задаются напрямую в коде:

1.Откройте файл scicosmo_bot.py.

2.Найдите блок **SETTINGS** в начале:
# ──────────────── SETTINGS ───────────────────────────

    BOT_TOKEN      = "PASTE_YOUR_BOT_TOKEN"

    CHANNEL_ID     = "@scicosmo_digest"

    TZ             = pytz.timezone("Europe/Kyiv")

    QUEUE_FILE     = Path("posts.json")

    POST_EVERY_SEC = 30

    OWNER_ID       = 123456789

3.Замените значения на свои:

BOT_TOKEN – токен от @BotFather

CHANNEL_ID – ваш канал (@имя_канала или числовой ID)

TZ – часовой пояс (оставьте "Europe/Kyiv" или укажите другой)

POST_EVERY_SEC – интервал проверки очереди в секундах

OWNER_ID – ваш Telegram user_id

4.Сохраните изменения и перезапустите бота.

---

## ▶️ Запуск

# Запускаем бота
python scicosmo_bot.py

---

##🤖 Команды

/start
Показывает главное меню с двумя кнопками:

~Создать пост

~Отменить посты

 ~Создать пост

1.Введите текст сообщения.

2.Прикрепите картинку или отправьте /skip.

3.Укажите дату и время в формате DD.MM.YYYY HH:MM.

~Отменить посты
Выводит список отложенных публикаций с кнопками ❌ для удаления.

~/cancel
Прерывает диалог создания поста.
