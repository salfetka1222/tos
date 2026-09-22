class GroupHandler:

    def __init__(self, bot, database, group_os):
        self.bot = bot
        self.database = database
        self.group_os = group_os

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
    # GROUP INFORMATION
    # =====================================================

    def get_group_chat(self, chat_id):

        response = self.bot.request(
            "getChat",
            {
                "chat_id": chat_id
            }
        )

        if not response or not response.get("ok"):
            return None

        return response.get("result", {})

    def is_group(self, chat_id):

        chat = self.get_group_chat(chat_id)

        if not chat:
            return False

        return chat.get("type") in (
            "group",
            "supergroup"
        )

    def get_group_member(
        self,
        chat_id,
        user_id
    ):

        response = self.bot.request(
            "getChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id
            }
        )

        if not response or not response.get("ok"):
            return None

        return response.get("result")

    def is_group_admin(
        self,
        chat_id,
        user_id
    ):

        member = self.get_group_member(
            chat_id,
            user_id
        )

        if not member:
            return False

        return member.get("status") in (
            "creator",
            "administrator"
        )

    def get_bot_member(self, chat_id):

        me_response = self.bot.request(
            "getMe",
            {}
        )

        if not me_response or not me_response.get("ok"):
            return None

        bot_user = me_response.get(
            "result",
            {}
        )

        bot_id = bot_user.get("id")

        if not bot_id:
            return None

        return self.get_group_member(
            chat_id,
            bot_id
        )

    # =====================================================
    # DASHBOARD
    # =====================================================

    def show_group_dashboard(
        self,
        chat_id,
        user_id
    ):

        chat_data = self.get_group_chat(chat_id)

        if not chat_data:

            self.send_message(
                chat_id,
                "❌ Не удалось получить информацию о группе."
            )

            return

        chat_type = chat_data.get(
            "type",
            "unknown"
        )

        if chat_type not in (
            "group",
            "supergroup"
        ):

            self.send_message(
                chat_id,
                (
                    "⚠️ <b>GROUP OS</b>\n\n"
                    "Group OS доступна только "
                    "в Telegram-группах."
                )
            )

            return

        title = chat_data.get(
            "title",
            "Без названия"
        )

        username = chat_data.get(
            "username"
        )

        if username:
            username = "@" + username
        else:
            username = "нет"

        members_response = self.bot.request(
            "getChatMemberCount",
            {
                "chat_id": chat_id
            }
        )

        if (
            members_response
            and members_response.get("ok")
        ):
            members = members_response.get(
                "result",
                "?"
            )
        else:
            members = "?"

        keyboard = [
            [
                {"text": "👥 Участники"},
                {"text": "🛡 Модерация"}
            ],
            [
                {"text": "📜 Журнал группы"},
                {"text": "⚙️ Права доступа"}
            ],
            [
                {"text": "🤖 Настройки ИИ"},
                {"text": "📊 Статистика группы"}
            ],
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "🖥️ <b>T-OS GROUP OS</b>\n\n"
                "🏠 <b>ПАНЕЛЬ ГРУППЫ</b>\n\n"
                f"📌 <b>Название:</b> {title}\n"
                f"🆔 <b>ID:</b> <code>{chat_id}</code>\n"
                f"💬 <b>Тип:</b> "
                f"{self.translate_chat_type(chat_type)}\n"
                f"🔗 <b>Username:</b> {username}\n"
                f"👥 <b>Участников:</b> {members}\n\n"
                "🟢 <b>T-OS:</b> АКТИВЕН\n\n"
                "⚙️ <b>МОДУЛИ GROUP OS</b>\n"
                "├ 👥 Участники\n"
                "├ 🛡 Модерация\n"
                "├ 📜 Журнал группы\n"
                "├ ⚙️ Права доступа\n"
                "├ 🤖 Настройки ИИ\n"
                "└ 📊 Статистика"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    def translate_chat_type(self, chat_type):

        types = {
            "group": "группа",
            "supergroup": "супергруппа",
            "private": "личный чат",
            "channel": "канал"
        }

        return types.get(
            chat_type,
            chat_type
        )

    # =====================================================
    # MEMBERS
    # =====================================================

    def show_group_members(
        self,
        chat_id,
        user_id
    ):

        if not self.is_group(chat_id):

            self.send_message(
                chat_id,
                "⚠️ Этот раздел работает только в группе."
            )

            return

        try:
            text = self.group_os.render_members(
                chat_id
            )
        except Exception as error:

            text = (
                "❌ Не удалось загрузить список участников.\n\n"
                f"<code>{error}</code>"
            )

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Назад в Group OS"},
                {"text": "🖥️ Главное меню"}
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
    # MODERATION
    # =====================================================

    def show_group_moderation(
        self,
        chat_id,
        user_id
    ):

        if not self.is_group(chat_id):

            self.send_message(
                chat_id,
                "⚠️ Модерация доступна только в группе."
            )

            return

        user_admin = self.is_group_admin(
            chat_id,
            user_id
        )

        bot_member = self.get_bot_member(
            chat_id
        )

        if bot_member:

            bot_status = bot_member.get(
                "status",
                "unknown"
            )

            bot_can_delete = bot_member.get(
                "can_delete_messages",
                False
            )

            bot_can_restrict = bot_member.get(
                "can_restrict_members",
                False
            )

            bot_can_promote = bot_member.get(
                "can_promote_members",
                False
            )

        else:

            bot_status = "unknown"
            bot_can_delete = False
            bot_can_restrict = False
            bot_can_promote = False

        user_status = (
            "🟢 Администратор"
            if user_admin
            else "👤 Участник"
        )

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Назад в Group OS"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "🛡️ <b>МОДЕРАЦИЯ</b>\n\n"
                f"👤 <b>Ваш статус:</b> {user_status}\n\n"
                f"🤖 <b>Статус бота:</b> {bot_status}\n\n"
                "🔐 <b>Права бота</b>\n"
                f"├ 🗑 Удаление сообщений: "
                f"{'🟢' if bot_can_delete else '🔴'}\n"
                f"├ 🔇 Ограничение участников: "
                f"{'🟢' if bot_can_restrict else '🔴'}\n"
                f"└ 👑 Управление администраторами: "
                f"{'🟢' if bot_can_promote else '🔴'}\n\n"
                "ℹ️ <i>Инструменты предупреждений, "
                "мутов и банов будут добавлены "
                "в следующий этап модуля.</i>"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # AUDIT LOG
    # =====================================================

    def show_group_audit_log(
        self,
        chat_id,
        user_id
    ):

        if not self.is_group(chat_id):

            self.send_message(
                chat_id,
                "⚠️ Журнал группы доступен только в группе."
            )

            return

        try:
            logs = self.group_os.get_audit_log(
                chat_id,
                limit=20
            )
        except Exception:
            logs = []

        lines = [
            "📜 <b>ЖУРНАЛ ГРУППЫ</b>",
            "",
            f"🆔 Группа: <code>{chat_id}</code>",
            ""
        ]

        if not logs:

            lines.extend([
                "📭 Записей пока нет.",
                "",
                "Новые действия Group OS будут "
                "появляться здесь."
            ])

        else:

            lines.append(
                f"📌 Последние события: <b>{len(logs)}</b>"
            )

            lines.append("")

            for log in logs:

                timestamp = log.get(
                    "created_at",
                    "?"
                )

                actor = log.get(
                    "user_id",
                    "?"
                )

                action = log.get(
                    "action",
                    "?"
                )

                target = log.get(
                    "target_id"
                )

                details = log.get(
                    "details",
                    ""
                )

                lines.append(
                    f"🕐 <code>{timestamp}</code>"
                )

                lines.append(
                    f"👤 <code>{actor}</code> → "
                    f"<b>{action}</b>"
                )

                if target:
                    lines.append(
                        f"🎯 Цель: <code>{target}</code>"
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
                {"text": "⬅️ Назад в Group OS"},
                {"text": "🖥️ Главное меню"}
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
    # PERMISSIONS
    # =====================================================

    def show_group_permissions(
        self,
        chat_id,
        user_id
    ):

        if not self.is_group(chat_id):

            self.send_message(
                chat_id,
                "⚠️ Права доступа доступны только в группе."
            )

            return

        user_member = self.get_group_member(
            chat_id,
            user_id
        )

        bot_member = self.get_bot_member(
            chat_id
        )

        user_status = (
            user_member.get(
                "status",
                "unknown"
            )
            if user_member
            else "unknown"
        )

        bot_status = (
            bot_member.get(
                "status",
                "unknown"
            )
            if bot_member
            else "unknown"
        )

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Назад в Group OS"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "⚙️ <b>ПРАВА ДОСТУПА</b>\n\n"
                "👤 <b>Ваш аккаунт</b>\n"
                f"Статус: "
                f"<b>{self.translate_member_status(user_status)}</b>\n\n"
                "🤖 <b>T-OS</b>\n"
                f"Статус: "
                f"<b>{self.translate_member_status(bot_status)}</b>\n\n"
                "🔐 <b>Уровни доступа</b>\n"
                "├ 👑 Владелец\n"
                "├ 🛡 Администратор\n"
                "├ 🔧 Модератор T-OS\n"
                "└ 👤 Участник\n\n"
                "ℹ️ Управление ролями T-OS будет "
                "добавлено после создания системы "
                "разрешений группы."
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    def translate_member_status(self, status):

        statuses = {
            "creator": "Владелец 👑",
            "administrator": "Администратор 🛡️",
            "member": "Участник 👤",
            "restricted": "Ограничен 🔇",
            "left": "Вышел",
            "kicked": "Заблокирован"
        }

        return statuses.get(
            status,
            status
        )

    # =====================================================
    # AI SETTINGS
    # =====================================================

    def show_group_ai_settings(
        self,
        chat_id,
        user_id
    ):

        if not self.is_group(chat_id):

            self.send_message(
                chat_id,
                "⚠️ Настройки ИИ доступны только в группе."
            )

            return

        try:
            settings = (
                self.group_os.get_settings(chat_id)
                or {}
            )
        except Exception:
            settings = {}

        ai_enabled = bool(
            settings.get(
                "ai_enabled",
                0
            )
        )

        ai_mode = settings.get(
            "ai_mode",
            "normal"
        )

        moderation_enabled = bool(
            settings.get(
                "moderation_enabled",
                0
            )
        )

        welcome_enabled = bool(
            settings.get(
                "welcome_enabled",
                0
            )
        )

        log_enabled = bool(
            settings.get(
                "log_enabled",
                1
            )
        )

        ai_status = (
            "🟢 Включён"
            if ai_enabled
            else "🔴 Выключен"
        )

        moderation_status = (
            "🟢 Включена"
            if moderation_enabled
            else "🔴 Выключена"
        )

        welcome_status = (
            "🟢 Включено"
            if welcome_enabled
            else "🔴 Выключено"
        )

        log_status = (
            "🟢 Включён"
            if log_enabled
            else "🔴 Выключен"
        )

        text = (
            "🤖 <b>НАСТРОЙКИ ИИ</b>\n\n"
            f"🧠 <b>T-OS AI:</b> {ai_status}\n"
            f"⚙️ <b>Режим:</b> <code>{ai_mode}</code>\n\n"
            "🛡 <b>Group OS</b>\n"
            f"├ Модерация: {moderation_status}\n"
            f"├ Приветствия: {welcome_status}\n"
            f"└ Журнал: {log_status}\n\n"
            "ℹ️ Настройки загружаются из базы данных "
            "Group OS."
        )

        keyboard = [
            [
                {
                    "text": (
                        "🔴 Выключить AI"
                        if ai_enabled
                        else "🟢 Включить AI"
                    )
                }
            ],
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Назад в Group OS"},
                {"text": "🖥️ Главное меню"}
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
    # STATISTICS
    # =====================================================

    def show_group_statistics(
        self,
        chat_id,
        user_id
    ):

        if not self.is_group(chat_id):

            self.send_message(
                chat_id,
                "⚠️ Статистика доступна только в группе."
            )

            return

        chat = self.get_group_chat(
            chat_id
        )

        members_response = self.bot.request(
            "getChatMemberCount",
            {
                "chat_id": chat_id
            }
        )

        if (
            members_response
            and members_response.get("ok")
        ):
            members = members_response.get(
                "result",
                "?"
            )
        else:
            members = "?"

        title = (
            chat.get(
                "title",
                "Без названия"
            )
            if chat
            else "Без названия"
        )

        try:

            statistics = self.group_os.get_statistics(
                chat_id
            )

            group_events = len(
                self.group_os.get_audit_log(
                    chat_id,
                    limit=100
                )
            )

            messages = statistics.get(
                "messages",
                0
            )

            commands = statistics.get(
                "commands",
                0
            )

            moderation_actions = statistics.get(
                "moderation_actions",
                0
            )

            ai_requests = statistics.get(
                "ai_requests",
                0
            )

        except Exception:

            statistics = {}
            group_events = 0
            messages = 0
            commands = 0
            moderation_actions = 0
            ai_requests = 0

        keyboard = [
            [
                {"text": "🔄 Обновить"}
            ],
            [
                {"text": "⬅️ Назад в Group OS"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "📊 <b>СТАТИСТИКА ГРУППЫ</b>\n\n"
                f"📌 <b>Название:</b> {title}\n"
                f"🆔 <b>ID:</b> <code>{chat_id}</code>\n\n"
                f"👥 <b>Участников:</b> {members}\n\n"
                "📈 <b>АКТИВНОСТЬ T-OS</b>\n"
                f"├ 💬 Сообщений: {messages}\n"
                f"├ ⌨️ Команд: {commands}\n"
                f"├ 🛡️ Модераций: {moderation_actions}\n"
                f"├ 🤖 Запросов к ИИ: {ai_requests}\n"
                f"└ 📜 Событий: {group_events}\n\n"
                "🟢 <b>Статус Group OS:</b> ACTIVE\n\n"
                "ℹ️ Счётчики Group OS "
                "будут автоматически расти "
                "по мере подключения событий."
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )