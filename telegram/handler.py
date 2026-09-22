from telegram.bot import TelegramBot


class TelegramHandler:
    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

    def handle_update(self, update):
        message = update.get("message")

        if not message:
            return

        text = message.get("text", "")
        chat_id = message["chat"]["id"]

        user = message.get("from", {})
        user_id = user.get("id")

        if user_id:
            self.database.create_user(
                user_id,
                user.get("username")
            )

        if text == "/start":
            self.show_home(chat_id)

        elif text == "📁 Файлы":
            self.show_files(chat_id, user_id)

        elif text == "📂 Desktop":
            self.show_directory(
                chat_id,
                user_id,
                "/home/user/Desktop"
            )

        elif text == "📂 Documents":
            self.show_directory(
                chat_id,
                user_id,
                "/home/user/Documents"
            )

        elif text == "📂 Downloads":
            self.show_directory(
                chat_id,
                user_id,
                "/home/user/Downloads"
            )

        elif text == "📂 Pictures":
            self.show_directory(
                chat_id,
                user_id,
                "/home/user/Pictures"
            )

        elif text == "📂 Projects":
            self.show_directory(
                chat_id,
                user_id,
                "/home/user/Projects"
            )

        elif text == "📂 Trash":
            self.show_directory(
                chat_id,
                user_id,
                "/home/user/Trash"
            )

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

        elif text == "🖥️ Главное меню":
            self.show_home(chat_id)

    def send_message(self, chat_id, text, keyboard=None):
        data = {
            "chat_id": chat_id,
            "text": text
        }

        if keyboard:
            data["reply_markup"] = {
                "keyboard": keyboard,
                "resize_keyboard": True
            }

        self.bot.request("sendMessage", data)

    def show_home(self, chat_id):
        keyboard = [
            [
                {"text": "📁 Файлы"},
                {"text": "📝 Заметки"}
            ],
            [
                {"text": "💻 Терминал"},
                {"text": "🧮 Калькулятор"}
            ],
            [
                {"text": "🎮 Игры"},
                {"text": "⚙️ Настройки"}
            ],
            [
                {"text": "👤 Профиль"},
                {"text": "📦 App Store"}
            ]
        ]

        self.send_message(
            chat_id,
            "🖥️ T-OS\n\n"
            "Добро пожаловать в операционную систему "
            "внутри Telegram.\n\n"
            "Выберите приложение:",
            keyboard
        )

    def initialize_filesystem(self, user_id):
        folders = [
            "/home/user/Desktop",
            "/home/user/Documents",
            "/home/user/Downloads",
            "/home/user/Pictures",
            "/home/user/Projects",
            "/home/user/Trash"
        ]

        for folder in folders:
            self.database.create_file(
                user_id,
                folder,
                file_type="directory"
            )

    def show_files(self, chat_id, user_id):
        self.initialize_filesystem(user_id)

        keyboard = [
            [
                {"text": "📂 Desktop"},
                {"text": "📂 Documents"}
            ],
            [
                {"text": "📂 Downloads"},
                {"text": "📂 Pictures"}
            ],
            [
                {"text": "📂 Projects"},
                {"text": "📂 Trash"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            "📁 ФАЙЛЫ T-OS\n\n"
            "📍 /home/user/\n\n"
            "Выберите папку:",
            keyboard
        )

    def show_directory(self, chat_id, user_id, directory):
        files = self.database.get_files(
            user_id,
            directory
        )

        name = directory.split("/")[-1]

        lines = [
            f"📂 {name}",
            "",
            f"📍 {directory}",
            ""
        ]

        found = False

        for file in files:
            path = file[1]
            file_type = file[2]

            if path.count("/") != directory.count("/") + 1:
                continue

            found = True

            filename = path.split("/")[-1]

            if file_type == "directory":
                lines.append(f"📂 {filename}")
            else:
                lines.append(f"📄 {filename}")

        if not found:
            lines.append("Папка пуста.")

        self.send_message(
            chat_id,
            "\n".join(lines),
            [
                [
                    {"text": "📁 Файлы"},
                    {"text": "🖥️ Главное меню"}
                ]
            ]
        )

    def show_profile(self, chat_id, message):
        user = message.get("from", {})

        user_id = user.get("id", "неизвестно")
        username = user.get("username")

        if username:
            username = f"@{username}"
        else:
            username = "не установлен"

        self.send_message(
            chat_id,
            "👤 ПРОФИЛЬ T-OS\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Username: {username}\n\n"
            "⭐ Уровень: 1\n"
            "✨ XP: 0\n"
            "🪙 T-Coins: 0"
        )

    def show_notes(self, chat_id):
        self.send_message(
            chat_id,
            "📝 ЗАМЕТКИ\n\n"
            "Система заметок T-OS находится в разработке."
        )

    def show_terminal(self, chat_id):
        self.send_message(
            chat_id,
            "💻 ТЕРМИНАЛ T-OS\n\n"
            "$ help\n"
            "$ ls\n"
            "$ cd\n"
            "$ mkdir\n"
            "$ touch\n"
            "$ cat\n"
            "$ rm\n"
            "$ clear"
        )

    def show_calculator(self, chat_id):
        self.send_message(
            chat_id,
            "🧮 КАЛЬКУЛЯТОР\n\n"
            "Калькулятор T-OS находится в разработке."
        )

    def show_games(self, chat_id):
        self.send_message(
            chat_id,
            "🎮 ИГРЫ T-OS\n\n"
            "🎲 Dice\n"
            "🧠 Quiz\n"
            "🔢 Guess Number\n"
            "🧩 Riddles\n"
            "⚡ Reaction"
        )

    def show_settings(self, chat_id):
        self.send_message(
            chat_id,
            "⚙️ НАСТРОЙКИ T-OS\n\n"
            "🌐 Язык: 🇷🇺 Русский\n"
            "🔔 Уведомления: включены\n"
            "🖥️ Режим: Personal OS"
        )

    def show_app_store(self, chat_id):
        self.send_message(
            chat_id,
            "📦 T-OS APP STORE\n\n"
            "💻 Terminal\n"
            "📝 Notes\n"
            "🎮 Games\n"
            "🧮 Calculator\n"
            "🌐 Network\n"
            "🤖 AI"
        )