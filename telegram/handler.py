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
            self.show_home(chat_id)

        elif text == "👤 Профиль":
            self.show_profile(chat_id, message)

    def show_home(self, chat_id):
        keyboard = {
            "keyboard": [
                [
                    {"text": "📁 Файлы"},
                    {"text": "📝 Заметки"},
                ],
                [
                    {"text": "💻 Терминал"},
                    {"text": "🧮 Калькулятор"},
                ],
                [
                    {"text": "🎮 Игры"},
                    {"text": "⚙️ Настройки"},
                ],
                [
                    {"text": "👤 Профиль"},
                    {"text": "📦 App Store"},
                ],
            ],
            "resize_keyboard": True
        }

        self.bot.request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": (
                    "🖥️ T-OS\n\n"
                    "Добро пожаловать в операционную систему "
                    "внутри Telegram.\n\n"
                    "Выберите приложение:"
                ),
                "reply_markup": keyboard,
            },
        )

    def show_profile(self, chat_id, message):
        user = message.get("from", {})

        user_id = user.get("id", "неизвестно")
        username = user.get("username")

        if username:
            username = f"@{username}"
        else:
            username = "не установлен"

        text = (
            "👤 ПРОФИЛЬ T-OS\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Username: {username}\n\n"
            "⭐ Уровень: 1\n"
            "✨ XP: 0\n"
            "🪙 T-Coins: 0"
        )

        self.bot.request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
            },
        )