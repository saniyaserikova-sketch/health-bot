import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =========================
# НАСТРОЙКИ
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

GOOGLE_CREDS_FILE = "credentials.json"   # файл ключа сервис-аккаунта
SPREADSHEET_NAME = "Health System"       # название таблицы
SHEET_NAME = "Daily"                     # лист

logging.basicConfig(level=logging.INFO)


# =========================
# GOOGLE SHEETS
# =========================

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_FILE, scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    return sheet


# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Health Bot активирован.")


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Да", "Нет"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Тест кнопок:",
        reply_markup=reply_markup,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat.id

    # Если кнопки
    if text in ["Да", "Нет"]:
        await update.message.reply_text(f"Ты нажала {text}")
        return

    # Пишем в Google Sheets
    try:
        sheet = get_sheet()
        sheet.append_row([datetime.now().isoformat(), text])
        await update.message.reply_text("Записано.")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Ошибка записи в таблицу.")


# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buttons", buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
