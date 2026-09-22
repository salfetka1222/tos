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

        elif text == "📁 Файлы":
            self.show_files(chat_id)

        elif text == "📝 Заметки":
            self.show_notes(chat_id)

        elif text == "💻 Терминал":
            self.show_terminal(chat_id)

        elif text == "🧮 Калькулятор":
            self.show_calculator(chat_id)

        elif text == "🎮 Игры":
            self.show_games(chat_id)

        elif text == "⚙️ Настройки":
            self.show_settings(chat_id)

        elif text == "👤 Профиль":
            self.show_profile(chat_id, message)

        elif text == "📦 App Store":
            self.show_app_store(chat_id)

    def send_message(self, chat_id, text):
        self.bot.request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
            },
        )

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
            "resize_keyboard": True,
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

        self.send_message(chat_id, text)

    def show_files(self, chat_id):
        self.send_message(
            chat_id,
            "📁 ФАЙЛЫ\n\n"
            "Домашняя папка:\n"
            "/home/user/\n\n"
            "📂 Desktop\n"
            "📂 Documents\n"
            "📂 Downloads\n"
            "📂 Pictures\n"
            "📂 Projects\n"
            "🗑️ Trash\n\n"
            "Виртуальная файловая система T-OS будет подключена здесь."
        )

    def show_notes(self, chat_id):
        self.send_message(
            chat_id,
            "📝 ЗАМЕТКИ\n\n"
            "Здесь будут храниться твои заметки T-OS.\n\n"
            "📌 Пока заметок нет.\n\n"
            "Система заметок будет подключена следующим этапом."
        )

    def show_terminal(self, chat_id):
        self.send_message(
            chat_id,
            "💻 ТЕРМИНАЛ T-OS\n\n"
            "$ help\n\n"
            "Доступные команды:\n"
            "$ ls\n"
            "$ cd\n"
            "$ mkdir\n"
            "$ touch\n"
            "$ cat\n"
            "$ rm\n"
            "$ clear\n"
            "$ run\n\n"
            "Виртуальный терминал будет подключён позже."
        )

    def show_calculator(self, chat_id):
        self.send_message(
            chat_id,
            "🧮 КАЛЬКУЛЯТОР\n\n"
            "Калькулятор T-OS готовится к запуску.\n\n"
            "Позже сюда добавим вычисления и историю операций."
        )

    def show_games(self, chat_id):
        self.send_message(
            chat_id,
            "🎮 ИГРЫ T-OS\n\n"
            "🎲 Dice\n"
            "🧠 Quiz\n"
            "🔢 Guess Number\n"
            "🧩 Riddles\n"
            "⚡ Reaction\n\n"
            "Игровая система будет подключена позже."
        )

    def show_settings(self, chat_id):
        self.send_message(
            chat_id,
            "⚙️ НАСТРОЙКИ T-OS\n\n"
            "🌐 Язык: 🇷🇺 Русский\n"
            "🔔 Уведомления: включены\n"
            "🖥️ Режим: Personal OS\n\n"
            "Настройки станут интерактивными на следующем этапе."
        )

    def show_app_store(self, chat_id):
        self.send_message(
            chat_id,
            "📦 T-OS APP STORE\n\n"
            "Популярные приложения:\n\n"
            "💻 Terminal\n"
            "📝 Notes\n"
            "🎮 Games\n"
            "🧮 Calculator\n"
            "🌐 Network\n"
            "🤖 AI\n\n"
            "Магазин приложений пока находится в разработке."
        )