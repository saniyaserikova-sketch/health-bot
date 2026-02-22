import os
import threading
import logging
from datetime import datetime

from flask import Flask

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO)

# ---------- ENV ----------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", "10000"))  # Render прокидывает PORT сам

GOOGLE_CREDS_FILE = "credentials.json"   # пока так; если положишь в src — скажи, поправим путь
SPREADSHEET_NAME = "Health System"
SHEET_NAME = "Daily"

# ---------- Flask (чтобы Render видел открытый порт) ----------
app = Flask(__name__)

@app.get("/")
def healthcheck():
    return "ok", 200


# ---------- Google Sheets ----------
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)


# ---------- Bot handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Health Bot активирован.")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Да", "Нет"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Тест кнопок:", reply_markup=reply_markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text in ["Да", "Нет"]:
        await update.message.reply_text(f"Ты нажала {text}")
        return

    try:
        sheet = get_sheet()
        sheet.append_row([datetime.now().isoformat(), text])
        await update.message.reply_text("Записано.")
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text("Ошибка записи в таблицу.")


def run_bot():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN is not set in Environment Variables")

    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("buttons", buttons))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logging.info("Bot polling started...")
    bot_app.run_polling()


# Запускаем polling в отдельном потоке, чтобы Flask мог держать порт
threading.Thread(target=run_bot, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
