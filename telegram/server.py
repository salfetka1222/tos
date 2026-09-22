from flask import Flask, request

from telegram.bot import TelegramBot
from telegram.handler import TelegramHandler
from database.database import Database


app = Flask(__name__)

database = Database()
database.initialize()

bot = TelegramBot()
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