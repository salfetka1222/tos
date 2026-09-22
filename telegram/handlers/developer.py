class DeveloperHandler:

    def __init__(self, bot, database, developer):
        self.bot = bot
        self.database = database
        self.developer = developer

    def send_message(
        self,
        chat_id,
        text,
        reply_markup=None
    ):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        if reply_markup:
            data["reply_markup"] = reply_markup

        try:
            return self.bot.request(
                "sendMessage",
                data
            )
        except Exception:
            return None

    def is_developer(self, user_id):
        try:
            return self.developer.is_developer(user_id)
        except Exception:
            return False

    def access_denied(self, chat_id):
        self.send_message(
            chat_id,
            (
                "❌ <b>Доступ запрещён.</b>\n\n"
                "Этот раздел доступен только разработчику."
            )
        )

    def show_panel(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        keyboard = {
            "keyboard": [
                [
                    {"text": "📊 Статистика"},
                    {"text": "👥 Пользователи"}
                ],
                [
                    {"text": "📜 Audit Log"},
                    {"text": "🗄 Database"}
                ],
                [
                    {"text": "🖥 System"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            (
                "🛠️ <b>T-OS DEVELOPER PANEL</b>\n\n"
                "🔐 Уровень доступа: <b>DEVELOPER</b>\n\n"
                "Выберите системный раздел:"
            ),
            keyboard
        )

    def show_statistics(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        try:
            stats = self.database.get_statistics()
        except Exception:
            stats = {
                "users": 0,
                "files": 0,
                "games": 0,
                "commands": 0,
                "audit_logs": 0
            }

        text = (
            "📊 <b>T-OS STATISTICS</b>\n\n"
            f"👥 Пользователи: <b>{stats['users']}</b>\n"
            f"📁 Файлы: <b>{stats['files']}</b>\n"
            f"🎮 Игр сыграно: <b>{stats['games']}</b>\n"
            f"⌨️ Команд: <b>{stats['commands']}</b>\n"
            f"📜 Audit Log: <b>{stats['audit_logs']}</b>"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"}
                ],
                [
                    {"text": "⬅️ Developer Panel"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def show_users(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        try:
            users = self.database.get_users()
        except Exception:
            users = []

        lines = [
            "👥 <b>T-OS USERS</b>",
            "",
            f"📌 Всего: <b>{len(users)}</b>",
            ""
        ]

        if not users:
            lines.append(
                "📭 Пользователей пока нет."
            )

        for user in users[:30]:

            username = user["username"]
            user_id_value = user["user_id"]
            level = user["level"]
            xp = user["xp"]
            coins = user["coins"]

            if username:
                name = f"@{username}"
            else:
                name = "Без username"

            lines.append(
                f"👤 <b>{name}</b>\n"
                f"   🆔 <code>{user_id_value}</code>\n"
                f"   ⭐ Level: <b>{level}</b>\n"
                f"   ✨ XP: <b>{xp}</b>\n"
                f"   🪙 Coins: <b>{coins}</b>"
            )

            lines.append("")

        text = "\n".join(lines)

        if len(text) > 3900:
            text = text[:3900] + "\n\n..."

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"}
                ],
                [
                    {"text": "⬅️ Developer Panel"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def show_audit_log(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        try:
            logs = self.database.get_audit_logs(
                limit=30
            )
        except Exception:
            logs = []

        lines = [
            "📜 <b>T-OS AUDIT LOG</b>",
            ""
        ]

        if not logs:
            lines.append(
                "📭 Журнал пока пуст."
            )

        for log in logs:

            actor = log["actor_id"]
            action = log["action"]
            target = log["target_id"]
            details = log["details"]
            created = log["created_at"]

            lines.append(
                f"🕐 <code>{created}</code>"
            )

            lines.append(
                f"👤 Actor: <code>{actor}</code>"
            )

            lines.append(
                f"⚙️ <b>{action}</b>"
            )

            if target is not None:
                lines.append(
                    f"🎯 Target: <code>{target}</code>"
                )

            if details:
                lines.append(
                    f"📝 {details}"
                )

            lines.append("")

        text = "\n".join(lines)

        if len(text) > 3900:
            text = text[:3900] + "\n\n..."

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"}
                ],
                [
                    {"text": "⬅️ Developer Panel"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def show_database(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        try:
            users = self.database.get_users()
        except Exception:
            users = []

        try:
            files = self.database.get_all_files()
        except Exception:
            files = []

        text = (
            "🗄️ <b>T-OS DATABASE</b>\n\n"
            "💾 Хранилище: <b>SQLite</b>\n"
            f"👥 Пользователей: <b>{len(users)}</b>\n"
            f"📁 Файлов: <b>{len(files)}</b>\n\n"
            "🟢 Database: <b>ONLINE</b>"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"}
                ],
                [
                    {"text": "⬅️ Developer Panel"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def show_system(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        text = (
            "🖥️ <b>T-OS SYSTEM</b>\n\n"
            "⚙️ Webhook: <b>ONLINE</b>\n"
            "🗄️ Database: <b>SQLite</b>\n"
            "📁 Filesystem: <b>ONLINE</b>\n"
            "💻 Terminal: <b>ONLINE</b>\n"
            "🤖 Group OS: <b>ONLINE</b>\n"
            "🎮 Games: <b>ONLINE</b>"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"}
                ],
                [
                    {"text": "⬅️ Developer Panel"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )