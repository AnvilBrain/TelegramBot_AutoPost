#!/usr/bin/env python3
# file: scicosmo_bot.py
# pip install "python-telegram-bot[job-queue]" pytz

import json
import logging
import uuid
import asyncio
from pathlib import Path
from datetime import datetime

import pytz
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes,
    filters, Defaults
)
from telegram.constants import ParseMode
from telegram.error import TimedOut

# ──────────────── SETTINGS ───────────────────────────
BOT_TOKEN      = "PASTE_YOUR_BOT_TOKEN"    # token from @BotFather
CHANNEL_ID     = "@scicosmo_digest"        # channel username or numeric ID
TZ             = pytz.timezone("Europe/Kyiv")
QUEUE_FILE     = Path("posts.json")
POST_EVERY_SEC = 30                        # check-interval in seconds
OWNER_ID       = 123456789                 # your Telegram user ID

# ──────────────── LOGGING ────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ──────────────── QUEUE HANDLING ─────────────────────
def load_queue() -> list[dict]:
    if QUEUE_FILE.exists():
        try:
            text = QUEUE_FILE.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else []
        except json.JSONDecodeError:
            log.warning("Invalid JSON in queue file, resetting queue.")
    return []

def save_queue(queue: list[dict]):
    QUEUE_FILE.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

queue: list[dict] = load_queue()

def enqueue_post(caption: str, photo_id: str | None, when_iso: str):
    post_id = str(uuid.uuid4())[:8]
    queue.append({"id": post_id, "caption": caption, "photo": photo_id, "when": when_iso})
    save_queue(queue)
    log.info("Queued %s at %s", post_id, when_iso)
    return post_id

def dequeue_post(post_id: str):
    global queue
    queue = [p for p in queue if p["id"] != post_id]
    save_queue(queue)
    log.info("Canceled %s", post_id)

# ──────────────── DIALOG STATES ─────────────────────
TEXT, PHOTO, WHEN = range(3)
KB_MAIN = ReplyKeyboardMarkup(
    [["Создать пост", "Отменить посты"]],
    resize_keyboard=True
)

# ──────────────── HANDLERS ───────────────────────────
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("Привет! Выбери действие:", reply_markup=KB_MAIN)

async def create_entry(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("Пришли текст поста:", reply_markup=ReplyKeyboardRemove())
    return TEXT

async def got_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    context.user_data["caption"] = update.message.text
    await update.message.reply_text("Отправь картинку или /skip")
    return PHOTO

async def got_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    context.user_data["photo"] = update.message.photo[-1].file_id
    await update.message.reply_text("Укажи дату и время DD.MM.YYYY HH:MM:")
    return WHEN

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    context.user_data["photo"] = None
    await update.message.reply_text("Укажи дату и время DD.MM.YYYY HH:MM:")
    return WHEN

async def got_when(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        dt = datetime.strptime(update.message.text.strip(), "%d.%m.%Y %H:%M")
        when = TZ.localize(dt)
    except ValueError:
        await update.message.reply_text("Неверный формат, попробуй ещё раз.")
        return WHEN

    post_id = enqueue_post(
        caption=context.user_data["caption"],
        photo_id=context.user_data["photo"],
        when_iso=when.isoformat()
    )
    await update.message.reply_text(f"✅ Пост добавлен (ID {post_id})", reply_markup=KB_MAIN)
    return ConversationHandler.END

async def cancel_conv(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("Отмена.", reply_markup=KB_MAIN)
    return ConversationHandler.END

async def list_posts(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not queue:
        await update.message.reply_text("Очередь пуста.", reply_markup=KB_MAIN)
        return
    buttons = [
        [InlineKeyboardButton(f"❌ {p['when'][:16]} — {p['caption'][:30]}…", callback_data=p["id"])]
        for p in queue
    ]
    await update.message.reply_text("Выбери пост:", reply_markup=InlineKeyboardMarkup(buttons))

async def cancel_post_cb(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.from_user.id != OWNER_ID:
        return
    q = update.callback_query
    await q.answer()
    dequeue_post(q.data)
    await q.edit_message_text("Пост отменён.")

# ──────────────── BACKGROUND TASK ───────────────────
async def poll_and_post(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TZ)
    for post in queue.copy():
        if datetime.fromisoformat(post["when"]) <= now:
            for attempt in range(3):
                try:
                    if post["photo"]:
                        await context.bot.send_photo(CHANNEL_ID, post["photo"], caption=post["caption"])
                    else:
                        await context.bot.send_message(CHANNEL_ID, post["caption"])
                    log.info("Posted %s", post["id"])
                    break
                except TimedOut:
                    log.warning("Timeout on post %s, retry %d", post["id"], attempt+1)
                    await asyncio.sleep(5)
                except Exception as e:
                    log.error("Error posting %s: %s", post["id"], e)
                    break
            dequeue_post(post["id"])

# ──────────────── MAIN ──────────────────────────────
def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .build()
    )

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Создать пост$"), create_entry)],
        states={
            TEXT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, got_text)],
            PHOTO: [MessageHandler(filters.PHOTO, got_photo), CommandHandler("skip", skip_photo)],
            WHEN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, got_when)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conv)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^Отменить посты$"), list_posts))
    app.add_handler(CallbackQueryHandler(cancel_post_cb))

    app.job_queue.run_repeating(poll_and_post, interval=POST_EVERY_SEC, first=5)

    log.info("Bot started…")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
