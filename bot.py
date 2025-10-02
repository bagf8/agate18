from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import os
from datetime import datetime

FILE_NAME = "congratulations.txt"
SECRET_CODE = "0410"
ADMIN_ID = 946997781  # <-- замени на свой Telegram ID

# --- сохранение/загрузка ---
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

# --- меню ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎂 Получить поздравления", callback_data="get")],
        [InlineKeyboardButton("🎁 Добавить поздравление", callback_data="add")],
        [InlineKeyboardButton("🗑 Удалить поздравление", callback_data="delete")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋! Выбери действие:", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    chat_id = update.message.chat_id
    message_id = update.message.message_id
    sender = user.username or user.first_name

    record = f"MSG::{chat_id}|{message_id}|{date}|{sender}"
    congratulations.append(record)
    save_all_congratulations()

    await update.message.reply_text(f"Поздравление сохранено 🎁 (ID: {len(congratulations)})")

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши так: /get КОД")
        return

    code = context.args[0]
    if code != SECRET_CODE:
        await update.message.reply_text("Неверный код 🚫")
        return

    if not congratulations:
        await update.message.reply_text("Пока поздравлений нет 🎂")
        return

    for i, congrats in enumerate(congratulations, start=1):
        if congrats.startswith("MSG::"):
            try:
                chat_id, message_id, date, sender = congrats.split("::", 1)[1].split("|", 3)
                await update.message.reply_text(f"[{i}] от {sender} ({date})")
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=chat_id,
                    message_id=int(message_id)
                )
            except Exception:
                await update.message.reply_text(f"[{i}] ❌ ошибка при пересылке")

# --- удаление ---
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для удаления 🚫")
        return

    if not context.args:
        await update.message.reply_text("Используй: /delete ID")
        return

    try:
        index = int(context.args[0]) - 1
        if 0 <= index < len(congratulations):
            removed = congratulations.pop(index)
            save_all_congratulations()
            await update.message.reply_text(f"Удалено поздравление: {removed}")
        else:
            await update.message.reply_text("Нет такого ID ❌")
    except ValueError:
        await update.message.reply_text("ID должен быть числом ❌")

# --- кнопки ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get":
        await query.edit_message_text("Чтобы получить поздравления, введи команду:\n/get КОД")
    elif query.data == "add":
        await query.edit_message_text("Просто отправь сообщение, и я его сохраню 🎉")
    elif query.data == "delete":
        await query.edit_message_text("Чтобы удалить, используй: /delete ID")
    elif query.data == "back":
        await query.edit_message_text("Привет 👋! Выбери действие:", reply_markup=main_menu())

# --- запуск ---
    import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# === твои функции ===
async def start(update, context):
    await update.message.reply_text("Привет! Я работаю на Render 🚀")

async def get(update, context):
    await update.message.reply_text("Функция get выполнена")

async def delete(update, context):
    await update.message.reply_text("Функция delete выполнена")

async def button(update, context):
    await update.callback_query.answer("Кнопка нажата")

async def handle_message(update, context):
    await update.message.reply_text(f"Ты написал: {update.message.text}")

# === Telegram Bot ===
def run_bot():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден. Укажи его в Render → Environment.")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get", get))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    app.run_polling()

# === Flask (для Render) ===
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "✅ Telegram bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# === Точка входа ===
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    # Запускаем Telegram-бота
    run_bot()
