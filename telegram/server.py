from flask import Flask, request

from telegram.bot import TelegramBot
from telegram.handler import TelegramHandler
from database.database import Database


app = Flask(__name__)

# Инициализация базы данных
database = Database()
database.initialize()

# Инициализация Telegram
bot = TelegramBot()

# Передаём bot и database в обработчик
handler = TelegramHandler(bot, database)


@app.get("/")
def index():
    return "T-OS is running"


@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True)

    if update:
        handler.handle_update(update)

    return {"ok": True}