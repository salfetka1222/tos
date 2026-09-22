from telegram.bot import TelegramBot
from datetime import datetime

from games import GamesSystem
from core.dev import DeveloperSystem
from core.group_os import GroupOS


class TelegramHandler:

    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

        self.games = GamesSystem(database)
        self.developer = DeveloperSystem(database)
        self.group_os = GroupOS(bot)

        self.file_states = {}
        self.terminal_dirs = {}
        self.command_history = {}

    # =====================================================
    # AUDIT
    # =====================================================

    def audit(
        self,
        actor_id,
        action,
        target_id=None,
        details=""
    ):
        try:
            self.database.add_audit_log(
                actor_id=actor_id,
                action=action,
                target_id=target_id,
                details=details
            )
        except Exception:
            pass

    # =====================================================
    # UPDATE
    # =====================================================

    def handle_update(self, update):

        message = update.get("message")

        if not message:
            return

        chat = message.get("chat", {})
        sender = message.get("from", {})

        chat_id = chat.get("id")
        user_id = sender.get("id")

        text = message.get("text", "").strip()

        if not chat_id or not user_id:
            return

        username = sender.get("username")

        self.database.create_user(
            user_id,
            username
        )

        if not self.database.has_achievement(
            user_id,
            "First Login"
        ):
            self.database.unlock_achievement(
                user_id,
                "First Login"
            )

        # =================================================
        # ACTIVE GAME
        # =================================================

        active_game = self.games.get_active_game(user_id)

        if active_game and text:

            result = None
            game_type = active_game.get("type")

            if game_type == "guess":
                result = self.games.check_guess(
                    user_id,
                    text
                )

            elif game_type == "quiz":
                result = self.games.check_quiz(
                    user_id,
                    text
                )

            elif game_type == "riddle":
                result = self.games.check_riddle(
                    user_id,
                    text
                )

            elif game_type == "reaction":
                result = self.games.check_reaction(
                    user_id,
                    text
                )

            if result:

                self.send_message(
                    chat_id,
                    result["message"]
                )

                if result.get("finished"):
                    self.show_games(
                        chat_id,
                        user_id
                    )

                return

        # =================================================
        # FILE INPUT
        # =================================================

        if user_id in self.file_states and text:

            state = self.file_states[user_id]

            if state["type"] == "filename":

                self.create_new_file(
                    chat_id,
                    user_id,
                    text
                )

                return

            if state["type"] == "editing":

                self.save_file_content(
                    chat_id,
                    user_id,
                    text
                )

                return

        # =================================================
        # TERMINAL
        # =================================================

        if text.startswith("$"):

            self.handle_terminal(
                chat_id,
                user_id,
                text
            )

            return

        # =================================================
        # DEVELOPER COMMAND
        # =================================================

        if text == "/dev":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                actor_id=user_id,
                action="developer_panel",
                details="Opened developer panel"
            )

            self.show_developer_panel(
                chat_id
            )

            return

        # =================================================
        # COMMANDS
        # =================================================

        if text == "/start":

            self.initialize_filesystem(
                user_id
            )

            self.show_home(
                chat_id
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

        # =================================================
        # GROUP OS
        # =================================================

        if text == "/group":

            self.show_group_dashboard(
                chat_id,
                user_id
            )

            return

        # =================================================
        # MAIN MENU
        # =================================================

        if text == "📁 Файлы":

            self.show_files(
                chat_id,
                user_id
            )
            return

        if text == "📝 Заметки":

            self.show_notes(chat_id)
            return

        if text == "💻 Терминал":

            self.show_terminal(
                chat_id,
                user_id
            )
            return

        if text == "🧮 Калькулятор":

            self.show_calculator(chat_id)
            return

        if text == "🎮 Игры":

            self.show_games(
                chat_id,
                user_id
            )
            return

        if text == "⚙️ Настройки":

            self.show_settings(chat_id)
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

        if text == "📦 App Store":

            self.show_app_store(chat_id)
            return

        if text == "🖥️ Главное меню":

            self.show_home(chat_id)
            return

        # =================================================
        # FILE MENU
        # =================================================

        if text == "➕ Новый файл":

            self.ask_filename(
                chat_id,
                user_id
            )
            return

        if text == "📂 Открыть":

            self.show_directory(
                chat_id,
                user_id,
                "/home/user"
            )
            return

        if text == "⬅️ Назад":

            self.show_files(
                chat_id,
                user_id
            )
            return

        # =================================================
        # GAME MENU
        # =================================================

        if text == "🎲 Dice":

            self.start_dice(
                chat_id,
                user_id
            )
            return

        if text == "🔢 Guess Number":

            self.start_guess(
                chat_id,
                user_id
            )
            return

        if text == "🧠 Quiz":

            self.start_quiz(
                chat_id,
                user_id
            )
            return

        if text == "🧩 Riddles":

            self.start_riddle(
                chat_id,
                user_id
            )
            return

        if text == "⚡ Reaction":

            self.start_reaction(
                chat_id,
                user_id
            )
            return

        if text == "❌ Выйти из игры":

            self.games.cancel_game(
                user_id
            )

            self.show_games(
                chat_id,
                user_id
            )
            return

        # =================================================
        # DEVELOPER PANEL
        # =================================================

        if text == "📊 Статистика":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                user_id,
                "view_statistics",
                details="Viewed system statistics"
            )

            self.show_developer_stats(
                chat_id
            )

            return

        if text == "👥 Пользователи":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                user_id,
                "view_users",
                details="Viewed user list"
            )

            self.show_developer_users(
                chat_id
            )

            return

        if text == "💾 База данных":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                user_id,
                "view_database",
                details="Viewed database information"
            )

            self.show_database_info(
                chat_id
            )

            return

        if text == "🧾 Audit Log":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                user_id,
                "view_audit_log",
                details="Viewed audit log"
            )

            self.show_audit_log(
                chat_id
            )

            return

        if text == "🧪 Experimental Lab":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                user_id,
                "view_experimental_lab",
                details="Opened Experimental Lab"
            )

            self.send_message(
                chat_id,
                (
                    "🧪 EXPERIMENTAL LAB\n\n"
                    "Экспериментальные функции пока отключены."
                )
            )

            return

        if text == "⚙️ Система":

            if not self.developer.is_developer(
                user_id
            ):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
                return

            self.audit(
                user_id,
                "view_system",
                details="Viewed system information"
            )

            self.show_system_info(
                chat_id
            )

            return

        # =================================================
        # UNKNOWN
        # =================================================

        self.send_message(
            chat_id,
            (
                "❓ Команда не распознана.\n\n"
                "Используй главное меню."
            )
        )

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
            "text": text
        }

        if reply_markup:
            data["reply_markup"] = reply_markup

        return self.bot.request(
            "sendMessage",
            data
        )

    # =====================================================
    # GROUP OS
    # =====================================================

    def show_group_dashboard(
        self,
        chat_id,
        user_id
    ):

        chat_response = self.bot.request(
            "getChat",
            {
                "chat_id": chat_id
            }
        )

        if not chat_response or not chat_response.get("ok"):

            self.send_message(
                chat_id,
                "❌ Не удалось получить информацию о группе."
            )

            return

        chat_data = chat_response.get(
            "result",
            {}
        )

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

        self.audit(
            actor_id=user_id,
            action="group_dashboard",
            target_id=chat_id,
            details="Opened Group OS dashboard"
        )

        keyboard = [
            [
                {"text": "👥 Members"},
                {"text": "🛡 Moderation"}
            ],
            [
                {"text": "📜 Group Audit Log"},
                {"text": "⚙️ Permissions"}
            ],
            [
                {"text": "🤖 AI Settings"},
                {"text": "📊 Statistics"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "🖥️ <b>T-OS GROUP OS</b>\n\n"
                "🏠 <b>GROUP DASHBOARD</b>\n\n"
                f"📌 <b>Название:</b> {title}\n"
                f"🆔 <b>ID:</b> <code>{chat_id}</code>\n"
                f"💬 <b>Тип:</b> {chat_type}\n"
                f"🔗 <b>Username:</b> {username}\n"
                f"👥 <b>Участников:</b> {members}\n\n"
                "🟢 <b>T-OS:</b> ACTIVE\n\n"
                "⚙️ <b>GROUP OS MODULES</b>\n"
                "├ 👥 Members\n"
                "├ 🛡 Moderation\n"
                "├ 📜 Group Audit Log\n"
                "├ ⚙️ Permissions\n"
                "├ 🤖 AI Settings\n"
                "└ 📊 Statistics"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # HOME
    # =====================================================

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
                {"text": "🏆 Достижения"}
            ],
            [
                {"text": "📦 App Store"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "🖥️ T-OS\n\n"
                "Добро пожаловать в T-OS.\n\n"
                "Выбери приложение:"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # DEVELOPER PANEL
    # =====================================================

    def show_developer_panel(self, chat_id):

        keyboard = [
            [
                {"text": "📊 Статистика"},
                {"text": "👥 Пользователи"}
            ],
            [
                {"text": "🎮 Игры"},
                {"text": "💾 База данных"}
            ],
            [
                {"text": "🧾 Audit Log"},
                {"text": "🧪 Experimental Lab"}
            ],
            [
                {"text": "⚙️ Система"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "🛠️ T-OS DEVELOPER PANEL\n\n"
                "Центр управления системой T-OS.\n\n"
                "Выбери раздел:"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    # =====================================================
    # DEVELOPER STATISTICS
    # =====================================================

    def show_developer_stats(self, chat_id):

        info = self.developer.get_system_info()

        self.send_message(
            chat_id,
            (
                "📊 T-OS STATISTICS\n\n"
                f"👥 Пользователей: {info['users']}\n"
                f"📁 Файлов: {info['files']}\n"
                f"🏆 Достижений: {info['achievements']}"
            )
        )

    # =====================================================
    # DEVELOPER USERS
    # =====================================================

    def show_developer_users(self, chat_id):

        users = self.developer.get_users(
            limit=20
        )

        if not users:

            self.send_message(
                chat_id,
                "👥 Пользователей пока нет."
            )

            return

        lines = [
            "👥 T-OS USERS",
            ""
        ]

        for user in users:

            username = user["username"]

            if username:
                name = f"@{username}"
            else:
                name = "без username"

            lines.append(
                f"• {name} | "
                f"ID: {user['user_id']} | "
                f"Lv.{user['level']}"
            )

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    # =====================================================
    # AUDIT LOG
    # =====================================================

    def show_audit_log(self, chat_id):

        logs = self.database.get_audit_logs(
            limit=20
        )

        if not logs:

            self.send_message(
                chat_id,
                (
                    "🧾 AUDIT LOG\n\n"
                    "Журнал пока пуст."
                )
            )

            return

        lines = [
            "🧾 T-OS AUDIT LOG",
            "",
            "Последние события:",
            ""
        ]

        for log in logs:

            timestamp = log["created_at"]
            actor = log["actor_id"]
            action = log["action"]
            target = log["target_id"]
            details = log["details"]

            line = (
                f"#{log['id']} | {timestamp}\n"
                f"👤 Actor: {actor}\n"
                f"⚙️ Action: {action}"
            )

            if target is not None:
                line += (
                    f"\n🎯 Target: {target}"
                )

            if details:
                line += (
                    f"\n📝 {details}"
                )

            lines.append(line)
            lines.append("")

        text = "\n".join(lines)

        if len(text) > 3900:
            text = text[:3900] + "\n\n..."

        self.send_message(
            chat_id,
            text
        )

    # =====================================================
    # DATABASE
    # =====================================================

    def show_database_info(self, chat_id):

        info = self.developer.get_system_info()

        self.send_message(
            chat_id,
            (
                "💾 DATABASE\n\n"
                "Engine: SQLite\n"
                f"Users: {info['users']}\n"
                f"Files: {info['files']}\n"
                f"Achievements: {info['achievements']}\n\n"
                "🟢 Database status: ONLINE"
            )
        )

    # =====================================================
    # SYSTEM
    # =====================================================

    def show_system_info(self, chat_id):

        info = self.developer.get_system_info()

        self.send_message(
            chat_id,
            (
                "⚙️ T-OS SYSTEM\n\n"
                "Status: 🟢 ONLINE\n"
                "Core: T-OS Core\n"
                "Database: SQLite\n"
                "Telegram: Connected\n\n"
                f"Users: {info['users']}\n"
                f"Files: {info['files']}\n"
                f"Achievements: {info['achievements']}"
            )
        )

    # =====================================================
    # FILE SYSTEM
    # =====================================================

    def initialize_filesystem(self, user_id):

        directories = [
            "/home",
            "/home/user",
            "/home/user/Desktop",
            "/home/user/Documents",
            "/home/user/Downloads",
            "/home/user/Pictures",
            "/home/user/Projects",
            "/home/user/Trash"
        ]

        for directory in directories:

            self.database.create_file(
                user_id,
                directory,
                file_type="directory"
            )

    def show_files(self, chat_id, user_id):

        self.initialize_filesystem(
            user_id
        )

        keyboard = [
            [
                {"text": "➕ Новый файл"},
                {"text": "📂 Открыть"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "📁 FILES\n\n"
                "/home/user/\n\n"
                "Выбери действие:"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    def ask_filename(self, chat_id, user_id):

        self.file_states[user_id] = {
            "type": "filename"
        }

        self.send_message(
            chat_id,
            (
                "📄 Создание файла\n\n"
                "Отправь имя файла.\n\n"
                "Например:\n"
                "hello.txt"
            )
        )

    def create_new_file(
        self,
        chat_id,
        user_id,
        filename
    ):

        self.file_states.pop(
            user_id,
            None
        )

        path = "/home/user/" + filename

        if self.database.path_exists(
            user_id,
            path
        ):

            self.send_message(
                chat_id,
                "❌ Такой файл уже существует."
            )

            return

        self.database.create_file(
            user_id,
            path,
            file_type="file",
            content=""
        )

        self.send_message(
            chat_id,
            (
                "✅ Файл создан:\n\n"
                f"{path}"
            )
        )

    def show_directory(
        self,
        chat_id,
        user_id,
        directory
    ):

        files = self.database.get_files(
            user_id,
            directory
        )

        if not files:

            self.send_message(
                chat_id,
                (
                    f"📂 {directory}\n\n"
                    "Папка пуста."
                )
            )

            return

        lines = [
            f"📂 {directory}",
            ""
        ]

        for item in files:

            name = item["path"].split("/")[-1]

            if item["file_type"] == "directory":
                lines.append(
                    f"📁 {name}"
                )
            else:
                lines.append(
                    f"📄 {name}"
                )

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    def open_file(
        self,
        chat_id,
        user_id,
        path
    ):

        file = self.database.get_file(
            user_id,
            path
        )

        if not file:

            self.send_message(
                chat_id,
                "❌ Файл не найден."
            )

            return

        if file["file_type"] == "directory":

            self.show_directory(
                chat_id,
                user_id,
                path
            )

            return

        self.send_message(
            chat_id,
            (
                f"📄 {path}\n\n"
                f"{file['content'] or '(пусто)'}"
            )
        )

    def start_editing(
        self,
        chat_id,
        user_id,
        path
    ):

        self.file_states[user_id] = {
            "type": "editing",
            "path": path
        }

        self.send_message(
            chat_id,
            (
                f"✏️ Редактирование:\n"
                f"{path}\n\n"
                "Отправь новое содержимое файла."
            )
        )

    def save_file_content(
        self,
        chat_id,
        user_id,
        content
    ):

        state = self.file_states.pop(
            user_id,
            None
        )

        if not state:
            return

        path = state["path"]

        self.database.update_file(
            user_id,
            path,
            content
        )

        self.send_message(
            chat_id,
            (
                "✅ Файл сохранён.\n\n"
                f"{path}"
            )
        )

    # =====================================================
    # TERMINAL
    # =====================================================

    def get_terminal_dir(self, user_id):

        return self.terminal_dirs.get(
            user_id,
            "/home/user"
        )

    def set_terminal_dir(
        self,
        user_id,
        path
    ):

        self.terminal_dirs[user_id] = path

    def normalize_path(
        self,
        user_id,
        path
    ):

        current = self.get_terminal_dir(
            user_id
        )

        if path.startswith("/"):
            result = path
        else:
            result = current.rstrip("/") + "/" + path

        parts = []

        for part in result.split("/"):

            if not part or part == ".":
                continue

            if part == "..":

                if parts:
                    parts.pop()

                continue

            parts.append(part)

        return "/" + "/".join(parts)

    def terminal_output(
        self,
        chat_id,
        text
    ):

        self.send_message(
            chat_id,
            f"```text\n{text}\n```"
        )

    def add_history(
        self,
        user_id,
        command
    ):

        history = self.command_history.setdefault(
            user_id,
            []
        )

        history.append(command)

        if len(history) > 50:
            history.pop(0)

    def handle_terminal(
        self,
        chat_id,
        user_id,
        text
    ):

        command_line = text[1:].strip()

        self.add_history(
            user_id,
            command_line
        )

        self.database.increment_commands(
            user_id
        )

        self.database.add_xp(
            user_id,
            1
        )

        self.database.unlock_achievement(
            user_id,
            "Terminal User"
        )

        user = self.database.get_user(
            user_id
        )

        if user and user["commands"] >= 100:

            self.database.unlock_achievement(
                user_id,
                "100 Commands"
            )

        if not command_line:

            self.terminal_output(
                chat_id,
                "T-OS Terminal"
            )

            return

        parts = command_line.split()

        command = parts[0].lower()
        args = parts[1:]

        if command == "help":

            self.terminal_output(
                chat_id,
                (
                    "T-OS Terminal\n\n"
                    "$ help\n"
                    "$ pwd\n"
                    "$ whoami\n"
                    "$ date\n"
                    "$ clear\n"
                    "$ ls\n"
                    "$ cd <path>\n"
                    "$ touch <file>\n"
                    "$ mkdir <dir>\n"
                    "$ cat <file>\n"
                    "$ write <file> <text>\n"
                    "$ echo <text>\n"
                    "$ rm <file>\n"
                    "$ cp <src> <dst>\n"
                    "$ mv <src> <dst>\n"
                    "$ tree\n"
                    "$ history\n"
                    "$ neofetch"
                )
            )
            return

        if command == "pwd":

            self.terminal_output(
                chat_id,
                self.get_terminal_dir(user_id)
            )
            return

        if command == "whoami":

            self.terminal_output(
                chat_id,
                str(user_id)
            )
            return

        if command == "date":

            self.terminal_output(
                chat_id,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            return

        if command == "clear":

            self.send_message(
                chat_id,
                "🧹 Terminal cleared."
            )
            return

        if command == "ls":

            directory = self.get_terminal_dir(
                user_id
            )

            files = self.database.get_files(
                user_id,
                directory
            )

            if not files:

                self.terminal_output(
                    chat_id,
                    "(empty)"
                )
                return

            lines = []

            for item in files:

                name = item["path"].split("/")[-1]

                if item["file_type"] == "directory":
                    lines.append(name + "/")
                else:
                    lines.append(name)

            self.terminal_output(
                chat_id,
                "\n".join(lines)
            )
            return

        if command == "cd":

            if not args:
                target = "/home/user"
            else:
                target = self.normalize_path(
                    user_id,
                    args[0]
                )

            file = self.database.get_file(
                user_id,
                target
            )

            if not file:

                self.terminal_output(
                    chat_id,
                    "cd: directory not found"
                )
                return

            if file["file_type"] != "directory":

                self.terminal_output(
                    chat_id,
                    "cd: not a directory"
                )
                return

            self.set_terminal_dir(
                user_id,
                target
            )
            return

        if command == "touch":

            if not args:

                self.terminal_output(
                    chat_id,
                    "touch: missing filename"
                )
                return

            path = self.normalize_path(
                user_id,
                args[0]
            )

            self.database.create_file(
                user_id,
                path
            )

            self.terminal_output(
                chat_id,
                "created: " + path
            )
            return

        if command == "mkdir":

            if not args:

                self.terminal_output(
                    chat_id,
                    "mkdir: missing directory"
                )
                return

            path = self.normalize_path(
                user_id,
                args[0]
            )

            self.database.create_file(
                user_id,
                path,
                file_type="directory"
            )

            self.terminal_output(
                chat_id,
                "created directory: " + path
            )
            return

        if command == "cat":

            if not args:

                self.terminal_output(
                    chat_id,
                    "cat: missing file"
                )
                return

            path = self.normalize_path(
                user_id,
                args[0]
            )

            file = self.database.get_file(
                user_id,
                path
            )

            if not file:

                self.terminal_output(
                    chat_id,
                    "cat: file not found"
                )
                return

            self.terminal_output(
                chat_id,
                file["content"] or "(empty)"
            )
            return

        if command == "write":

            if len(args) < 2:

                self.terminal_output(
                    chat_id,
                    "write: usage: $ write <file> <text>"
                )
                return

            path = self.normalize_path(
                user_id,
                args[0]
            )

            content = " ".join(args[1:])

            if not self.database.path_exists(
                user_id,
                path
            ):
                self.database.create_file(
                    user_id,
                    path
                )

            self.database.update_file(
                user_id,
                path,
                content
            )

            self.terminal_output(
                chat_id,
                "saved: " + path
            )
            return

        if command == "echo":

            self.terminal_output(
                chat_id,
                " ".join(args)
            )
            return

        if command == "rm":

            if not args:

                self.terminal_output(
                    chat_id,
                    "rm: missing file"
                )
                return

            path = self.normalize_path(
                user_id,
                args[0]
            )

            if not self.database.path_exists(
                user_id,
                path
            ):

                self.terminal_output(
                    chat_id,
                    "rm: not found"
                )
                return

            self.database.delete_file(
                user_id,
                path
            )

            self.terminal_output(
                chat_id,
                "removed: " + path
            )
            return

        if command == "cp":

            if len(args) < 2:

                self.terminal_output(
                    chat_id,
                    "cp: usage: $ cp <src> <dst>"
                )
                return

            source = self.normalize_path(
                user_id,
                args[0]
            )

            destination = self.normalize_path(
                user_id,
                args[1]
            )

            file = self.database.get_file(
                user_id,
                source
            )

            if not file:

                self.terminal_output(
                    chat_id,
                    "cp: source not found"
                )
                return

            self.database.create_file(
                user_id,
                destination,
                file_type=file["file_type"],
                content=file["content"]
            )

            self.terminal_output(
                chat_id,
                "copied"
            )
            return

        if command == "mv":

            if len(args) < 2:

                self.terminal_output(
                    chat_id,
                    "mv: usage: $ mv <src> <dst>"
                )
                return

            source = self.normalize_path(
                user_id,
                args[0]
            )

            destination = self.normalize_path(
                user_id,
                args[1]
            )

            file = self.database.get_file(
                user_id,
                source
            )

            if not file:

                self.terminal_output(
                    chat_id,
                    "mv: source not found"
                )
                return

            self.database.create_file(
                user_id,
                destination,
                file_type=file["file_type"],
                content=file["content"]
            )

            self.database.delete_file(
                user_id,
                source
            )

            self.terminal_output(
                chat_id,
                "moved"
            )
            return

        if command == "tree":

            directory = self.get_terminal_dir(
                user_id
            )

            output = self.build_tree(
                user_id,
                directory
            )

            self.terminal_output(
                chat_id,
                output or "(empty)"
            )
            return

        if command == "history":

            history = self.command_history.get(
                user_id,
                []
            )

            if not history:

                self.terminal_output(
                    chat_id,
                    "(empty)"
                )
                return

            lines = []

            for index, item in enumerate(
                history,
                start=1
            ):
                lines.append(
                    f"{index}  {item}"
                )

            self.terminal_output(
                chat_id,
                "\n".join(lines)
            )
            return

        if command == "neofetch":

            user = self.database.get_user(
                user_id
            )

            self.terminal_output(
                chat_id,
                (
                    "████████████████\n"
                    "T-OS\n\n"
                    f"User: {user['username'] or 'unknown'}\n"
                    f"Level: {user['level']}\n"
                    f"XP: {user['xp']}\n"
                    f"Coins: {user['coins']}\n"
                    f"Commands: {user['commands']}\n"
                    "Database: SQLite\n"
                    "Core: T-OS"
                )
            )
            return

        self.terminal_output(
            chat_id,
            f"command not found: {command}"
        )

    def build_tree(
        self,
        user_id,
        directory
    ):

        files = self.database.get_files(
            user_id,
            directory
        )

        if not files:
            return ""

        lines = []

        for item in files:

            name = item["path"].split("/")[-1]

            if item["file_type"] == "directory":
                lines.append(
                    "📁 " + name + "/"
                )
            else:
                lines.append(
                    "📄 " + name
                )

        return "\n".join(lines)

    def show_terminal(
        self,
        chat_id,
        user_id
    ):

        self.initialize_filesystem(
            user_id
        )

        self.set_terminal_dir(
            user_id,
            "/home/user"
        )

        self.send_message(
            chat_id,
            (
                "💻 T-OS TERMINAL\n\n"
                "Терминал готов.\n\n"
                "Примеры:\n"
                "$ help\n"
                "$ ls\n"
                "$ pwd\n"
                "$ neofetch\n\n"
                "Все файлы являются виртуальными."
            )
        )

    # =====================================================
    # PROFILE
    # =====================================================

    def show_profile(
        self,
        chat_id,
        user_id
    ):

        user = self.database.get_user(
            user_id
        )

        if not user:
            return

        username = user["username"]

        if username:
            username = "@" + username
        else:
            username = "без username"

        self.send_message(
            chat_id,
            (
                "👤 T-OS PROFILE\n\n"
                f"Username: {username}\n"
                f"ID: {user['user_id']}\n\n"
                f"⭐ Level: {user['level']}\n"
                f"XP: {user['xp']}\n"
                f"🪙 T-Coins: {user['coins']}\n\n"
                f"⌨️ Commands: {user['commands']}\n"
                f"🎮 Games: {user['games_played']}\n"
                f"🏆 Wins: {user['games_won']}"
            )
        )

    # =====================================================
    # ACHIEVEMENTS
    # =====================================================

    def show_achievements(
        self,
        chat_id,
        user_id
    ):

        achievements = self.database.get_achievements(
            user_id
        )

        if not achievements:

            self.send_message(
                chat_id,
                (
                    "🏆 ACHIEVEMENTS\n\n"
                    "Пока достижений нет."
                )
            )
            return

        lines = [
            "🏆 ACHIEVEMENTS",
            ""
        ]

        for achievement in achievements:

            lines.append(
                "🏅 " + achievement["achievement"]
            )

        self.send_message(
            chat_id,
            "\n".join(lines)
        )

    # =====================================================
    # NOTES
    # =====================================================

    def show_notes(self, chat_id):

        self.send_message(
            chat_id,
            (
                "📝 NOTES\n\n"
                "Система заметок пока находится "
                "в разработке."
            )
        )

    # =====================================================
    # CALCULATOR
    # =====================================================

    def show_calculator(self, chat_id):

        self.send_message(
            chat_id,
            (
                "🧮 CALCULATOR\n\n"
                "Калькулятор будет подключён "
                "на следующем этапе."
            )
        )

    # =====================================================
    # SETTINGS
    # =====================================================

    def show_settings(self, chat_id):

        self.send_message(
            chat_id,
            (
                "⚙️ SETTINGS\n\n"
                "Настройки T-OS находятся "
                "в разработке."
            )
        )

    # =====================================================
    # APP STORE
    # =====================================================

    def show_app_store(self, chat_id):

        self.send_message(
            chat_id,
            (
                "📦 T-OS APP STORE\n\n"
                "Магазин приложений пока пуст.\n\n"
                "SDK и система приложений будут "
                "добавлены позже."
            )
        )

    # =====================================================
    # GAMES
    # =====================================================

    def show_games(
        self,
        chat_id,
        user_id
    ):

        keyboard = [
            [
                {"text": "🎲 Dice"},
                {"text": "🔢 Guess Number"}
            ],
            [
                {"text": "🧠 Quiz"},
                {"text": "🧩 Riddles"}
            ],
            [
                {"text": "⚡ Reaction"}
            ],
            [
                {"text": "❌ Выйти из игры"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            (
                "🎮 T-OS GAMES\n\n"
                "Выбери игру:"
            ),
            {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        )

    def start_dice(
        self,
        chat_id,
        user_id
    ):

        result, won = self.games.start_dice(
            user_id
        )

        if won:

            message = (
                "🎲 DICE\n\n"
                f"Результат: {result}\n\n"
                "🎉 Победа!\n"
                "⭐ +10 XP\n"
                "🪙 +10 T-Coins"
            )

        else:

            message = (
                "🎲 DICE\n\n"
                f"Результат: {result}\n\n"
                "😔 Не повезло.\n"
                "⭐ +10 XP\n"
                "🪙 +2 T-Coins"
            )

        self.send_message(
            chat_id,
            message
        )

    def start_guess(
        self,
        chat_id,
        user_id
    ):

        self.send_message(
            chat_id,
            self.games.start_guess(
                user_id
            )
        )

    def start_quiz(
        self,
        chat_id,
        user_id
    ):

        self.send_message(
            chat_id,
            self.games.start_quiz(
                user_id
            )
        )

    def start_riddle(
        self,
        chat_id,
        user_id
    ):

        self.send_message(
            chat_id,
            self.games.start_riddle(
                user_id
            )
        )

    def start_reaction(
        self,
        chat_id,
        user_id
    ):

        self.send_message(
            chat_id,
            self.games.start_reaction(
                user_id
            )
        )