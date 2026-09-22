class DeveloperHandler:

    def __init__(self, bot, database, developer):
        self.bot = bot
        self.database = database
        self.developer = developer

    # =====================================================
    # TELEGRAM
    # =====================================================

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

        return self.bot.request(
            "sendMessage",
            data
        )

    # =====================================================
    # ACCESS
    # =====================================================

    def is_developer(self, user_id):
        try:
            return self.developer.is_developer(user_id)
        except Exception:
            return False

    def access_denied(self, chat_id):
        self.send_message(
            chat_id,
            "❌ <b>Доступ запрещён.</b>\n\n"
            "Этот раздел доступен только разработчику."
        )

    # =====================================================
    # DEVELOPER PANEL
    # =====================================================

    def show_panel(self, chat_id, user_id):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        keyboard = [
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
        ]

        self.send_message(
            chat_id,
            (
                "🛠️ <b>T-OS DEVELOPER PANEL</b>\n\n"
                "🔐 Уровень доступа: "
                "<b>DEVELOPER</b>\n\n"
                "Выберите системный раздел:"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # STATISTICS
    # =====================================================

    def show_statistics(
        self,
        chat_id,
        user_id
    ):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        try:
            stats = self.database.get_statistics()
        except Exception:
            stats = {}

        users = stats.get("users", 0)
        messages = stats.get("messages", 0)
        games = stats.get("games", 0)
        files = stats.get("files", 0)

        text = (
            "📊 <b>T-OS STATISTICS</b>\n\n"
            f"👥 Пользователи: <b>{users}</b>\n"
            f"💬 Сообщения: <b>{messages}</b>\n"
            f"🎮 Игры: <b>{games}</b>\n"
            f"📁 Файлы: <b>{files}</b>"
        )

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Developer Panel"}
            ],
            [
                {"text": "🏠 Главная"}
            ]
        ]

        self.send_message(
            chat_id,
            text,
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # USERS
    # =====================================================

    def show_users(
        self,
        chat_id,
        user_id
    ):

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
            f"📌 Всего пользователей: <b>{len(users)}</b>",
            ""
        ]

        if not users:
            lines.append(
                "📭 Пользователей пока нет."
            )

        else:
            for user in users[:30]:

                username = user.get(
                    "username"
                )

                first_name = user.get(
                    "first_name"
                )

                user_id_value = user.get(
                    "user_id",
                    "?"
                )

                if username:
                    name = f"@{username}"
                elif first_name:
                    name = first_name
                else:
                    name = "Без имени"

                lines.append(
                    f"👤 <b>{name}</b>\n"
                    f"   🆔 <code>{user_id_value}</code>"
                )

                lines.append("")

        text = "\n".join(lines)

        if len(text) > 3900:
            text = text[:3900] + "\n\n..."

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Developer Panel"}
            ],
            [
                {"text": "🏠 Главная"}
            ]
        ]

        self.send_message(
            chat_id,
            text,
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # AUDIT LOG
    # =====================================================

    def show_audit_log(
        self,
        chat_id,
        user_id
    ):

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

        else:

            for log in logs:

                action = log.get(
                    "action",
                    "unknown"
                )

                actor = log.get(
                    "user_id",
                    "?"
                )

                created = log.get(
                    "created_at",
                    "?"
                )

                details = log.get(
                    "details",
                    ""
                )

                lines.append(
                    f"🕐 <code>{created}</code>"
                )

                lines.append(
                    f"👤 <code>{actor}</code>"
                )

                lines.append(
                    f"⚙️ <b>{action}</b>"
                )

                if details:
                    lines.append(
                        f"📝 {details}"
                    )

                lines.append("")

        text = "\n".join(lines)

        if len(text) > 3900:
            text = text[:3900] + "\n\n..."

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Developer Panel"}
            ],
            [
                {"text": "🏠 Главная"}
            ]
        ]

        self.send_message(
            chat_id,
            text,
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # DATABASE
    # =====================================================

    def show_database(
        self,
        chat_id,
        user_id
    ):

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
            "💾 <b>Хранилище:</b> SQLite\n"
            f"👥 Пользователей: <b>{len(users)}</b>\n"
            f"📁 Файлов: <b>{len(files)}</b>\n\n"
            "🟢 <b>Database:</b> ONLINE"
        )

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Developer Panel"}
            ],
            [
                {"text": "🏠 Главная"}
            ]
        ]

        self.send_message(
            chat_id,
            text,
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # SYSTEM
    # =====================================================

    def show_system(
        self,
        chat_id,
        user_id
    ):

        if not self.is_developer(user_id):
            self.access_denied(chat_id)
            return

        text = (
            "🖥️ <b>T-OS SYSTEM</b>\n\n"
            "⚙️ <b>Режим:</b> Telegram Webhook\n"
            "🗄️ <b>Database:</b> SQLite\n"
            "🤖 <b>Group OS:</b> подключена\n"
            "🎮 <b>Games:</b> подключены\n\n"
            "🟢 <b>System:</b> ONLINE"
        )

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Developer Panel"}
            ],
            [
                {"text": "🏠 Главная"}
            ]
        ]

        self.send_message(
            chat_id,
            text,
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )