from flask import Flask, request

from telegram.bot import TelegramBot
from telegram.handler import TelegramHandler


app = Flask(__name__)

bot = TelegramBot()
handler = TelegramHandler(bot)


@app.get("/")
def index():
    return "T-OS is running"


@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True)

    if update:
        handler.handle_update(update)

    return {"ok": True}