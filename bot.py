import os
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# === Настройки ===
FILE_NAME = "congratulations.txt"
SECRET_CODE = "0410"
ADMIN_ID = 946997781  # твой Telegram ID

# === Работа с файлом ===
def load_congratulations():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []

def save_all_congratulations():
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        for congrats in congratulations:
            f.write(congrats + "\n")

congratulations = load_congratulations()

# === Функции бота ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎂 Получить поздравления", callback_data="get")],
        [InlineKeyboardButton("🎁 Добавить поздравление", callback_data="add")],
        [InlineKeyboardButton("🗑 Удалить поздравление", callback_data="delete")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет 👋! Выбери действие в меню:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    username = f"@{user.username}" if user.username else user.first_name
    file_id, content, message_type = None, "", ""

    if update.message.text:
        message_type, content = "Текст", update.message.text
    elif update.message.photo:
        message_type, file_id, content = "Фото", update.message.photo[-1].file_id, "[Фото]"
    elif update.message.video:
        message_type, file_id, content = "Видео", update.message.video.file_id, "[Видео]"
    elif update.message.voice:
        message_type, file_id, content = "Голосовое", update.message.voice.file_id, "[Голосовое]"
    else:
        message_type, content = "Другое", "[Вложение]"

    congrats = f"{date} | {username} ({user.id}) | {message_type}: {content}"
    congratulations.append(congrats)
    if file_id:
        congratulations.append(f"file_id: {file_id}")

    save_all_congratulations()
    await update.message.reply_text(f"✅ Поздравление сохранено (ID: {len(congratulations)})")

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /get КОД")
        return
    if context.args[0] != SECRET_CODE:
        await update.message.reply_text("🚫 Неверный код")
        return
    if not congratulations:
        await update.message.reply_text("🎂 Пока поздравлений нет")
        return

    for i, congrats in enumerate(congratulations, start=1):
        if not congrats.startswith("file_id:"):
            await update.message.reply_text(f"[{i}] {congrats}")
        else:
            file_id = congrats.split("file_id: ")[1]
            try:
                await update.message.reply_photo(file_id)
            except:
                try:
                    await update.message.reply_video(file_id)
                except:
                    try:
                        await update.message.reply_voice(file_id)
                    except:
                        await update.message.reply_text("[Ошибка при отправке файла]")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 У вас нет прав для удаления")
        return
    if not context.args:
        await update.message.reply_text("Используй: /delete ID")
        return
    try:
        idx = int(context.args[0]) - 1
        if 0 <= idx < len(congratulations):
            removed = congratulations.pop(idx)
            save_all_congratulations()
            await update.message.reply_text(f"🗑 Удалено: {removed}")
        else:
            await update.message.reply_text("🚫 Неверный ID")
    except ValueError:
        await update.message.reply_text("ID должен быть числом")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "get":
        await query.edit_message_text("Чтобы получить поздравления, напиши:\n/get КОД")
    elif query.data == "add":
        await query.edit_message_text("Просто отправь сообщение, и я его сохраню 🎉")
    elif query.data == "delete":
        await query.edit_message_text("Удалить можно через: /delete ID")

# === Flask + Webhook ===
app_flask = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render подставит

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("get", get))
application.add_handler(CommandHandler("delete", delete))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

@app_flask.route("/")
def home():
    return "✅ Telegram bot is running on Render!"

@app_flask.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

# === Запуск ===
if __name__ == "__main__":
    # Устанавливаем webhook при старте
    asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}"))
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
