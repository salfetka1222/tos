from telegram.bot import TelegramBot

from games import GamesSystem
from core.dev import DeveloperSystem
from core.group_os import GroupOS

from telegram.handlers.group import GroupHandler
from telegram.handlers.developer import DeveloperHandler
from telegram.handlers.filesystem import FilesystemHandler


class TelegramHandler:

    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

        self.games = GamesSystem(database)
        self.developer = DeveloperSystem(database)
        self.group_os = GroupOS(bot, database)

        self.group = GroupHandler(
            bot,
            database,
            self.group_os
        )

        self.file_states = {}
        self.terminal_dirs = {}
        self.command_history = {}

    # =========================================================
    # UPDATE ROUTER
    # =========================================================

    def handle_update(self, update):
        message = update.get("message")

        if not message:
            return

        chat = message.get("chat", {})
        sender = message.get("from", {})

        chat_id = chat.get("id")
        user_id = sender.get("id")

        if not chat_id or not user_id:
            return

        text = message.get("text", "").strip()

        # =====================================================
        # USER
        # =====================================================

        try:
            self.database.get_or_create_user(
                user_id,
                sender.get("username"),
                sender.get("first_name")
            )
        except Exception:
            pass

        # =====================================================
        # ACTIVE GAME
        # =====================================================

        if user_id in getattr(self.games, "active_games", {}):
            try:
                if self.games.handle_input(user_id, text):
                    return
            except Exception:
                pass

        # =====================================================
        # FILE INPUT
        # =====================================================

        if user_id in self.file_states:
            try:
                if self.handle_file_input(
                    chat_id,
                    user_id,
                    text
                ):
                    return
            except Exception:
                pass

        # =====================================================
        # TERMINAL
        # =====================================================

        if text.startswith("$"):
            self.handle_terminal(
                chat_id,
                user_id,
                text
            )
            return

        # =====================================================
        # DEVELOPER COMMAND
        # =====================================================

        if text == "/dev":
            self.show_developer_panel(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # BASIC COMMANDS
        # =====================================================

        if text == "/start":
            self.show_home(
                chat_id,
                user_id,
                clear=True
            )
            return

        if text == "/profile":
            self.show_profile(
                chat_id,
                user_id
            )
            return

        if text == "/achievements":
            self.show_achievements(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # GROUP OS
        # =====================================================

        if text == "/group":
            self.group.show_group_dashboard(
                chat_id,
                user_id
            )
            return

        if text == "👥 Участники":
            self.group.show_group_members(
                chat_id,
                user_id
            )
            return

        if text == "🛡 Модерация":
            self.group.show_group_moderation(
                chat_id,
                user_id
            )
            return

        if text == "📜 Журнал группы":
            self.group.show_group_audit_log(
                chat_id,
                user_id
            )
            return

        if text == "⚙️ Права доступа":
            self.group.show_group_permissions(
                chat_id,
                user_id
            )
            return

        if text == "🤖 Настройки ИИ":
            self.group.show_group_ai_settings(
                chat_id,
                user_id
            )
            return

        if text == "📊 Статистика группы":
            self.group.show_group_statistics(
                chat_id,
                user_id
            )
            return

        if text == "🔄 Обновить":
            self.group.show_group_dashboard(
                chat_id,
                user_id
            )
            return

        if text == "⬅️ Назад в Group OS":
            self.group.show_group_dashboard(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # MAIN MENU
        # =====================================================

        if text == "🏠 Главная":
            self.show_home(
                chat_id,
                user_id
            )
            return
            
        if text == "🖥️ Главное меню":
            self.show_home(
                chat_id,
                user_id
            )
            return

        if text == "📁 Файловая система":
            self.show_filesystem(
                chat_id,
                user_id
            )
            return

        if text == "💻 Терминал":
            self.show_terminal(
                chat_id,
                user_id
            )
            return

        if text == "👤 Профиль":
            self.show_profile(
                chat_id,
                user_id
            )
            return

        if text == "🏆 Достижения":
            self.show_achievements(
                chat_id,
                user_id
            )
            return

        if text == "📝 Заметки":
            self.show_notes(
                chat_id,
                user_id
            )
            return

        if text == "🧮 Калькулятор":
            self.show_calculator(
                chat_id,
                user_id
            )
            return

        if text == "⚙️ Настройки":
            self.show_settings(
                chat_id,
                user_id
            )
            return

        if text == "🛍 App Store":
            self.show_app_store(
                chat_id,
                user_id
            )
            return

        if text == "🎮 Игры":
            self.show_games(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # FILE SYSTEM
        # =====================================================

        if text == "📄 Создать файл":
            self.create_file_start(
                chat_id,
                user_id
            )
            return

        if text == "📂 Мои файлы":
            self.show_files(
                chat_id,
                user_id
            )
            return

        if text == "📁 Создать папку":
            self.create_folder_start(
                chat_id,
                user_id
            )
            return

        if text == "⬅️ Назад":
            self.show_home(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # GAMES
        # =====================================================

        if text == "🎯 Играть":
            self.start_game(
                chat_id,
                user_id
            )
            return

        if text == "📊 Статистика игр":
            self.show_game_statistics(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # DEVELOPER PANEL
        # =====================================================

        if text == "🛠 Dev Panel":
            self.show_developer_panel(
                chat_id,
                user_id
            )
            return

        if text == "📊 Статистика":
            self.show_developer_statistics(
                chat_id,
                user_id
            )
            return

        if text == "👥 Пользователи":
            self.show_developer_users(
                chat_id,
                user_id
            )
            return

        if text == "📜 Audit Log":
            self.show_audit_log(
                chat_id,
                user_id
            )
            return

        if text == "🗄 Database":
            self.show_database(
                chat_id,
                user_id
            )
            return

        if text == "🖥 System":
            self.show_system(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # UNKNOWN
        # =====================================================

        self.handle_unknown(
            chat_id,
            user_id,
            text
        )

    # =========================================================
    # HOME
    # =========================================================

    def show_home(self, chat_id, user_id, clear=False):
        if clear:
            try:
                self.database.clear_user_context(user_id)
            except Exception:
                pass

        text = (
            "🖥 <b>T-OS</b>\n\n"
            "Добро пожаловать в виртуальную операционную систему.\n\n"
            "Выберите нужный раздел:"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "📁 Файловая система"},
                    {"text": "💻 Терминал"}
                ],
                [
                    {"text": "👤 Профиль"},
                    {"text": "🏆 Достижения"}
                ],
                [
                    {"text": "📝 Заметки"},
                    {"text": "🧮 Калькулятор"}
                ],
                [
                    {"text": "🎮 Игры"},
                    {"text": "👥 Group OS"}
                ],
                [
                    {"text": "⚙️ Настройки"},
                    {"text": "🛍 App Store"}
                ]
            ],
            "resize_keyboard": True
        }

        self.bot.request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": keyboard
            }
        )

    # =========================================================
    # DEVELOPER PANEL
    # =========================================================

    def show_developer_panel(self, chat_id, user_id):
        if not self.developer.is_developer(user_id):
            self.send_message(
                chat_id,
                "❌ Доступ к Developer Panel запрещён."
            )
            return

        text = (
            "🛠 <b>DEVELOPER PANEL</b>\n\n"
            "Выберите раздел:"
        )

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
            text,
            keyboard
        )

    def show_developer_statistics(self, chat_id, user_id):
        if not self.developer.is_developer(user_id):
            self.send_message(
                chat_id,
                "❌ Доступ запрещён."
            )
            return

        try:
            stats = self.database.get_statistics()
        except Exception:
            stats = {}

        text = (
            "📊 <b>СТАТИСТИКА T-OS</b>\n\n"
            f"👥 Пользователи: <b>{stats.get('users', 0)}</b>\n"
            f"💬 Сообщения: <b>{stats.get('messages', 0)}</b>\n"
            f"🎮 Игры: <b>{stats.get('games', 0)}</b>\n"
            f"📁 Файлы: <b>{stats.get('files', 0)}</b>"
        )

        self.send_message(chat_id, text)

    def show_developer_users(self, chat_id, user_id):
        if not self.developer.is_developer(user_id):
            self.send_message(
                chat_id,
                "❌ Доступ запрещён."
            )
            return

        try:
            users = self.database.get_users()
        except Exception:
            users = []

        lines = [
            "👥 <b>ПОЛЬЗОВАТЕЛИ</b>",
            ""
        ]

        for user in users[:30]:
            username = user.get("username") or "без username"
            lines.append(
                f"• {username}"
            )

        if len(lines) == 2:
            lines.append("Пользователей пока нет.")

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    def show_audit_log(self, chat_id, user_id):
        if not self.developer.is_developer(user_id):
            self.send_message(
                chat_id,
                "❌ Доступ запрещён."
            )
            return

        try:
            logs = self.database.get_audit_logs(limit=30)
        except Exception:
            logs = []

        lines = [
            "📜 <b>AUDIT LOG</b>",
            ""
        ]

        if not logs:
            lines.append("Журнал пуст.")

        for log in logs:
            action = log.get("action", "unknown")
            uid = log.get("user_id", "?")
            created = log.get("created_at", "")

            lines.append(
                f"• <b>{action}</b>\n"
                f"  👤 {uid}\n"
                f"  🕒 {created}"
            )

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    def show_database(self, chat_id, user_id):
        if not self.developer.is_developer(user_id):
            self.send_message(
                chat_id,
                "❌ Доступ запрещён."
            )
            return

        text = (
            "🗄 <b>DATABASE</b>\n\n"
            "Основная база данных T-OS работает через SQLite."
        )

        self.send_message(
            chat_id,
            text
        )

    def show_system(self, chat_id, user_id):
        if not self.developer.is_developer(user_id):
            self.send_message(
                chat_id,
                "❌ Доступ запрещён."
            )
            return

        text = (
            "🖥 <b>SYSTEM</b>\n\n"
            "T-OS работает в режиме Telegram Webhook."
        )

        self.send_message(
            chat_id,
            text
        )

    # =========================================================
    # PROFILE
    # =========================================================

    def show_profile(self, chat_id, user_id):
        try:
            user = self.database.get_user(user_id)
        except Exception:
            user = None

        if not user:
            self.send_message(
                chat_id,
                "❌ Профиль не найден."
            )
            return

        username = user.get("username") or "нет"
        first_name = user.get("first_name") or "Пользователь"
        xp = user.get("xp", 0)
        coins = user.get("coins", 0)

        text = (
            "👤 <b>ПРОФИЛЬ</b>\n\n"
            f"Имя: <b>{first_name}</b>\n"
            f"Username: <b>{username}</b>\n\n"
            f"⭐ XP: <b>{xp}</b>\n"
            f"🪙 Монеты: <b>{coins}</b>"
        )

        self.send_message(
            chat_id,
            text
        )

    # =========================================================
    # ACHIEVEMENTS
    # =========================================================

    def show_achievements(self, chat_id, user_id):
        try:
            achievements = self.database.get_user_achievements(
                user_id
            )
        except Exception:
            achievements = []

        lines = [
            "🏆 <b>ДОСТИЖЕНИЯ</b>",
            ""
        ]

        if not achievements:
            lines.append(
                "У вас пока нет полученных достижений."
            )
        else:
            for achievement in achievements:
                name = achievement.get(
                    "name",
                    "Достижение"
                )
                lines.append(
                    f"🏆 {name}"
                )

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    # =========================================================
    # FILE SYSTEM
    # =========================================================

    def show_filesystem(self, chat_id, user_id):
        text = (
            "📁 <b>ФАЙЛОВАЯ СИСТЕМА</b>\n\n"
            "Выберите действие:"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "📂 Мои файлы"},
                    {"text": "📄 Создать файл"}
                ],
                [
                    {"text": "📁 Создать папку"}
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

    def show_files(self, chat_id, user_id):
        try:
            files = self.database.get_user_files(
                user_id
            )
        except Exception:
            files = []

        lines = [
            "📂 <b>МОИ ФАЙЛЫ</b>",
            ""
        ]

        if not files:
            lines.append(
                "Файлов пока нет."
            )
        else:
            for file in files:
                name = file.get(
                    "name",
                    "Без имени"
                )
                lines.append(
                    f"📄 {name}"
                )

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    def create_file_start(self, chat_id, user_id):
        self.file_states[user_id] = {
            "action": "create_file"
        }

        self.send_message(
            chat_id,
            "📄 Введите имя нового файла:"
        )

    def create_folder_start(self, chat_id, user_id):
        self.file_states[user_id] = {
            "action": "create_folder"
        }

        self.send_message(
            chat_id,
            "📁 Введите имя новой папки:"
        )

    def handle_file_input(self, chat_id, user_id, text):
        state = self.file_states.get(user_id)

        if not state:
            return False

        action = state.get("action")

        if action == "create_file":
            try:
                self.database.create_file(
                    user_id,
                    text
                )

                self.send_message(
                    chat_id,
                    f"✅ Файл <b>{text}</b> создан."
                )
            except Exception:
                self.send_message(
                    chat_id,
                    "❌ Не удалось создать файл."
                )

            del self.file_states[user_id]
            return True

        if action == "create_folder":
            try:
                self.database.create_path(
                    user_id,
                    text
                )

                self.send_message(
                    chat_id,
                    f"✅ Папка <b>{text}</b> создана."
                )
            except Exception:
                self.send_message(
                    chat_id,
                    "❌ Не удалось создать папку."
                )

            del self.file_states[user_id]
            return True

        return False

    # =========================================================
    # TERMINAL
    # =========================================================

    def show_terminal(self, chat_id, user_id):
        text = (
            "💻 <b>TERMINAL</b>\n\n"
            "Введите команду с префиксом <code>$</code>.\n\n"
            "Например:\n"
            "<code>$ help</code>"
        )

        self.send_message(
            chat_id,
            text
        )

    def handle_terminal(self, chat_id, user_id, text):
        command = text[1:].strip()

        if not command:
            self.send_message(
                chat_id,
                "💻 Введите команду после <code>$</code>."
            )
            return

        self.command_history.setdefault(
            user_id,
            []
        ).append(command)

        if command == "help":
            output = (
                "💻 <b>TERMINAL HELP</b>\n\n"
                "$ help\n"
                "$ pwd\n"
                "$ ls\n"
                "$ clear"
            )

        elif command == "pwd":
            output = (
                self.terminal_dirs.get(
                    user_id,
                    "/"
                )
            )

        elif command == "ls":
            output = "📁 Пусто."

        elif command == "clear":
            output = "🧹 Терминал очищен."

        else:
            output = (
                f"❌ Команда не найдена: "
                f"<code>{command}</code>"
            )

        self.send_message(
            chat_id,
            output
        )

    # =========================================================
    # NOTES
    # =========================================================

    def show_notes(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "📝 <b>ЗАМЕТКИ</b>\n\n"
            "Раздел заметок пока находится в разработке."
        )

    # =========================================================
    # CALCULATOR
    # =========================================================

    def show_calculator(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "🧮 <b>КАЛЬКУЛЯТОР</b>\n\n"
            "Раздел калькулятора готовится."
        )

    # =========================================================
    # SETTINGS
    # =========================================================

    def show_settings(self, chat_id, user_id):
        text = (
            "⚙️ <b>НАСТРОЙКИ</b>\n\n"
            "Настройки T-OS."
        )

        self.send_message(
            chat_id,
            text
        )

    # =========================================================
    # APP STORE
    # =========================================================

    def show_app_store(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "🛍 <b>APP STORE</b>\n\n"
            "Магазин приложений T-OS находится в разработке."
        )

    # =========================================================
    # GAMES
    # =========================================================

    def show_games(self, chat_id, user_id):
        text = (
            "🎮 <b>ИГРЫ</b>\n\n"
            "Выберите действие:"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🎯 Играть"},
                    {"text": "📊 Статистика игр"}
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

    def start_game(self, chat_id, user_id):
        try:
            result = self.games.start_game(
                user_id
            )

            if result:
                self.send_message(
                    chat_id,
                    result
                )
                return
        except Exception:
            pass

        self.send_message(
            chat_id,
            "🎮 Запуск игры..."
        )

    def show_game_statistics(self, chat_id, user_id):
        try:
            stats = self.database.get_game_statistics(
                user_id
            )
        except Exception:
            stats = {}

        text = (
            "📊 <b>СТАТИСТИКА ИГР</b>\n\n"
            f"🎮 Игр: <b>{stats.get('games', 0)}</b>\n"
            f"🏆 Побед: <b>{stats.get('wins', 0)}</b>\n"
            f"⭐ XP: <b>{stats.get('xp', 0)}</b>"
        )

        self.send_message(
            chat_id,
            text
        )

    # =========================================================
    # UNKNOWN
    # =========================================================

    def handle_unknown(self, chat_id, user_id, text):
        self.send_message(
            chat_id,
            "🤔 Неизвестная команда.\n\n"
            "Используйте меню T-OS или /start."
        )

    # =========================================================
    # SEND MESSAGE
    # =========================================================

    def send_message(
        self,
        chat_id,
        text,
        keyboard=None
    ):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        if keyboard:
            data["reply_markup"] = keyboard

        try:
            return self.bot.request(
                "sendMessage",
                data
            )
        except Exception:
            return None