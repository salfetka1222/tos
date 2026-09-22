from telegram.bot import TelegramBot


class TelegramHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle_update(self, update):
        message = update.get("message")

        if not message:
            return

        text = message.get("text", "")
        chat_id = message["chat"]["id"]

        if text == "/start":
            self.bot.request(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": "🖥️ Добро пожаловать в T-OS!\n\nСистема запускается...",
                },
            )