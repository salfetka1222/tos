import os
import sqlite3
from datetime import datetime, timedelta

from telegram.bot import TelegramBot
from games import GamesSystem
from core.dev import DeveloperSystem



# =========================================================
# DEVELOPER CONFIG
# =========================================================

# Добавь DEVELOPER_ID в Railway Variables.
# Пример:
# DEVELOPER_ID = 123456789
#
# Сам ID сюда мне присылать не нужно.
try:
    DEVELOPER_ID = int(
        os.getenv("DEVELOPER_ID", "0")
    )
except ValueError:
    DEVELOPER_ID = 8063619759


class TelegramHandler:
    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

        self.games = GamesSystem(database)
        self.developer = DeveloperSystem(database)
        
        self.file_states = {}
        self.terminal_dirs = {}
        self.command_history = {}

        self.file_states = {}
        self.terminal_dirs = {}
        self.command_history = {}

        # Временное состояние Developer Panel
        self.developer_states = {}

        self.initialize_developer_system()

    # =========================================================
    # DEVELOPER SYSTEM
    # =========================================================

    def initialize_developer_system(self):
        """
        Создаёт служебные таблицы Developer Panel.
        database.py менять не требуется.
        """

        with self.database.connect() as connection:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_id INTEGER NOT NULL,
                    target_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_restrictions (
                    user_id INTEGER PRIMARY KEY,
                    until TIMESTAMP NOT NULL,
                    reason TEXT DEFAULT '',
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.commit()

    def is_developer(self, user_id):
        return (
            DEVELOPER_ID != 0
            and user_id == DEVELOPER_ID
        )

    def audit(
        self,
        actor_id,
        action,
        target_id=None,
        details=""
    ):
        try:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO audit_log
                    (actor_id, target_id, action, details)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        actor_id,
                        target_id,
                        action,
                        details
                    )
                )

                connection.commit()

        except Exception:
            # Ошибка аудита не должна ломать T-OS
            pass

    def is_restricted(self, user_id):
        try:
            with self.database.connect() as connection:

                row = connection.execute(
                    """
                    SELECT until
                    FROM user_restrictions
                    WHERE user_id = ?
                    """,
                    (user_id,)
                ).fetchone()

                if not row:
                    return False

                until = datetime.fromisoformat(
                    row[0]
                )

                if datetime.now() >= until:
                    connection.execute(
                        """
                        DELETE FROM user_restrictions
                        WHERE user_id = ?
                        """,
                        (user_id,)
                    )

                    connection.commit()

                    return False

                return True

        except Exception:
            return False

    def get_restriction(self, user_id):
        try:
            with self.database.connect() as connection:

                row = connection.execute(
                    """
                    SELECT
                        user_id,
                        until,
                        reason,
                        created_by,
                        created_at
                    FROM user_restrictions
                    WHERE user_id = ?
                    """,
                    (user_id,)
                ).fetchone()

                return row

        except Exception:
            return None

    def restrict_user(
        self,
        actor_id,
        target_id,
        minutes,
        reason=""
    ):
        until = (
            datetime.now()
            + timedelta(minutes=minutes)
        )

        with self.database.connect() as connection:

            connection.execute(
                """
                INSERT OR REPLACE INTO user_restrictions
                (user_id, until, reason, created_by)
                VALUES (?, ?, ?, ?)
                """,
                (
                    target_id,
                    until.isoformat(),
                    reason,
                    actor_id
                )
            )

            connection.commit()

        self.audit(
            actor_id,
            "USER_RESTRICTED",
            target_id,
            f"{minutes} min; {reason}"
        )

    def unrestrict_user(
        self,
        actor_id,
        target_id
    ):
        with self.database.connect() as connection:

            connection.execute(
                """
                DELETE FROM user_restrictions
                WHERE user_id = ?
                """,
                (target_id,)
            )

            connection.commit()

        self.audit(
            actor_id,
            "USER_UNRESTRICTED",
            target_id
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def handle_update(self, update):
        message = update.get("message")

        if not message:
            return

        text = message.get("text", "")
        chat_id = message["chat"]["id"]

        user = message.get("from", {})
        user_id = user.get("id")

        if not user_id:
            return

        username = user.get("username")

        self.database.create_user(
            user_id,
            username
        )

        self.database.unlock_achievement(
            user_id,
            "First Login"
        )

        # =====================================================
        # RESTRICTION CHECK
        # =====================================================

        if not self.is_developer(user_id):

            restriction = self.get_restriction(
                user_id
            )

            if restriction:

                until = datetime.fromisoformat(
                    restriction["until"]
                    if isinstance(
                        restriction,
                        sqlite3.Row
                    )
                    else restriction[1]
                )

                if datetime.now() < until:

                    reason = (
                        restriction["reason"]
                        if isinstance(
                            restriction,
                            sqlite3.Row
                        )
                        else restriction[2]
                    )

                    self.send_message(
                        chat_id,
                        "🚫 ДОСТУП ОГРАНИЧЕН\n\n"
                        f"До: {until.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Причина: {reason or 'не указана'}"
                    )
                    return

        # =====================================================
        # DEVELOPER COMMANDS
        # =====================================================

        if text == "/dev":
            if not self.developer.is_developer(user_id):
                self.send_message(
                    chat_id,
                    "⛔ Доступ запрещён."
                )
            return
            
            self.show_developer_panel(chat_id)
            return

        if text == "/myid":
            self.send_message(
                chat_id,
                f"🆔 Ваш Telegram ID: {user_id}"
            )
            return

        # =====================================================
        # DEVELOPER PANEL BUTTONS
        # =====================================================

        if self.is_developer(user_id):

            if text == "🛡️ Developer Panel":
                self.show_developer_panel(
                    chat_id,
                    user_id
                )
                return

            if text == "📊 Статистика":
                self.show_developer_stats(
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

            if text == "🎮 Игры":
                self.show_developer_games(
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

            if text == "🚫 Ограничения":
                self.show_restrictions(
                    chat_id,
                    user_id
                )
                return

            if text == "⚙️ System Info":
                self.show_system_info(
                    chat_id,
                    user_id
                )
                return

            if text == "⬅️ Назад":
                self.show_developer_panel(
                    chat_id,
                    user_id
                )
                return

            if text == "🖥️ T-OS":
                self.show_home(chat_id)
                return

        # =====================================================
        # ACTIVE GAME
        # =====================================================

        active_game = self.games.get_active_game(
            user_id
        )

        if active_game:
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

        # =====================================================
        # FILE STATES
        # =====================================================

        state = self.file_states.get(user_id)

        if state == "waiting_filename":
            self.create_new_file(
                chat_id,
                user_id,
                text
            )
            return

        if state and state.startswith("editing:"):

            path = state.replace(
                "editing:",
                "",
                1
            )

            self.save_file_content(
                chat_id,
                user_id,
                path,
                text
            )
            return

        if state and state.startswith("opened:"):

            if text == "✏️ Редактировать":

                path = state.replace(
                    "opened:",
                    "",
                    1
                )

                self.start_editing(
                    chat_id,
                    user_id,
                    path
                )
                return

            if text == "📁 Файлы":

                self.file_states.pop(
                    user_id,
                    None
                )

                self.show_files(
                    chat_id,
                    user_id
                )
                return

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
        # COMMANDS
        # =====================================================

        if text == "/start":

            self.file_states.pop(
                user_id,
                None
            )

            self.games.cancel_game(
                user_id
            )

            self.database.add_xp(
                user_id,
                10
            )

            self.show_home(
                chat_id,
                user_id
            )

        elif text == "/profile":

            self.show_profile(
                chat_id,
                message
            )

        elif text == "/achievements":

            self.show_achievements(
                chat_id,
                user_id
            )

        # =====================================================
        # MENU
        # =====================================================

        elif text == "📁 Файлы":

            self.file_states.pop(
                user_id,
                None
            )

            self.games.cancel_game(
                user_id
            )

            self.show_files(
                chat_id,
                user_id
            )

        elif text == "📄 Создать файл":

            self.ask_filename(
                chat_id,
                user_id
            )

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

            self.games.cancel_game(
                user_id
            )

            self.show_notes(
                chat_id
            )

        elif text == "💻 Терминал":

            self.games.cancel_game(
                user_id
            )

            self.show_terminal(
                chat_id,
                user_id
            )

        elif text == "🧮 Калькулятор":

            self.games.cancel_game(
                user_id
            )

            self.show_calculator(
                chat_id
            )

        elif text == "🎮 Игры":

            self.show_games(
                chat_id,
                user_id
            )

        # =====================================================
        # GAME MENU
        # =====================================================

        elif text == "🎲 Dice":

            self.start_dice(
                chat_id,
                user_id
            )

        elif text == "🔢 Guess Number":

            self.start_guess(
                chat_id,
                user_id
            )

        elif text == "🧠 Quiz":

            self.start_quiz(
                chat_id,
                user_id
            )

        elif text == "🧩 Riddles":

            self.start_riddle(
                chat_id,
                user_id
            )

        elif text == "⚡ Reaction":

            self.start_reaction(
                chat_id,
                user_id
            )

        elif text == "❌ Выйти из игры":

            self.games.cancel_game(
                user_id
            )

            self.show_games(
                chat_id,
                user_id
            )

        elif text == "⚙️ Настройки":

            self.games.cancel_game(
                user_id
            )

            self.show_settings(
                chat_id
            )

        elif text == "👤 Профиль":

            self.games.cancel_game(
                user_id
            )

            self.show_profile(
                chat_id,
                message
            )

        elif text == "🏆 Достижения":

            self.show_achievements(
                chat_id,
                user_id
            )

        elif text == "📦 App Store":

            self.games.cancel_game(
                user_id
            )

            self.show_app_store(
                chat_id
            )

        elif text == "🖥️ Главное меню":

            self.file_states.pop(
                user_id,
                None
            )

            self.games.cancel_game(
                user_id
            )

            self.show_home(
                chat_id,
                user_id
            )

        elif text.startswith("📄 "):

            filename = text[2:].strip()

            self.open_file(
                chat_id,
                user_id,
                f"/home/user/Documents/{filename}"
            )

    # =========================================================
    # DEVELOPER PANEL
    # =========================================================

    def show_developer_panel(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        self.audit(
            user_id,
            "OPEN_DEVELOPER_PANEL"
        )

        keyboard = [
            [
                {"text": "📊 Статистика"},
                {"text": "👥 Пользователи"}
            ],
            [
                {"text": "🎮 Игры"},
                {"text": "📜 Audit Log"}
            ],
            [
                {"text": "🚫 Ограничения"},
                {"text": "⚙️ System Info"}
            ],
            [
                {"text": "🖥️ T-OS"}
            ]
        ]

        self.send_message(
            chat_id,
            "🛡️ T-OS DEVELOPER PANEL\n\n"
            "Добро пожаловать в системный центр "
            "разработчика.\n\n"
            "Здесь находятся инструменты управления "
            "и диагностики T-OS.",
            keyboard
        )

    def show_developer_stats(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        with self.database.connect() as connection:

            users = connection.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            commands = connection.execute(
                "SELECT COALESCE(SUM(commands), 0) FROM users"
            ).fetchone()[0]

            games_played = connection.execute(
                "SELECT COALESCE(SUM(games_played), 0) FROM users"
            ).fetchone()[0]

            games_won = connection.execute(
                "SELECT COALESCE(SUM(games_won), 0) FROM users"
            ).fetchone()[0]

            xp = connection.execute(
                "SELECT COALESCE(SUM(xp), 0) FROM users"
            ).fetchone()[0]

            coins = connection.execute(
                "SELECT COALESCE(SUM(coins), 0) FROM users"
            ).fetchone()[0]

            audit_count = connection.execute(
                "SELECT COUNT(*) FROM audit_log"
            ).fetchone()[0]

        self.audit(
            user_id,
            "VIEW_STATISTICS"
        )

        keyboard = [
            [
                {"text": "⬅️ Назад"}
            ]
        ]

        self.send_message(
            chat_id,
            "📊 T-OS STATISTICS\n\n"
            f"👥 Пользователей: {users}\n"
            f"⌨️ Команд: {commands}\n"
            f"🎮 Игр сыграно: {games_played}\n"
            f"🏆 Побед: {games_won}\n"
            f"✨ Всего XP: {xp}\n"
            f"🪙 T-Coins: {coins}\n"
            f"📜 Audit events: {audit_count}",
            keyboard
        )

    def show_developer_users(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        with self.database.connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    user_id,
                    username,
                    level,
                    xp,
                    coins,
                    commands,
                    games_played,
                    games_won
                FROM users
                ORDER BY xp DESC
                LIMIT 20
                """
            ).fetchall()

        self.audit(
            user_id,
            "VIEW_USERS"
        )

        lines = [
            "👥 T-OS USERS",
            "",
            "Показаны первые 20 пользователей:",
            ""
        ]

        if not rows:
            lines.append(
                "Пользователей пока нет."
            )

        for index, row in enumerate(
            rows,
            start=1
        ):
            username = (
                f"@{row['username']}"
                if row["username"]
                else "без username"
            )

            restriction = self.get_restriction(
                row["user_id"]
            )

            status = (
                "🔴 Restricted"
                if restriction
                else "🟢 Active"
            )

            lines.append(
                f"{index}. {status}\n"
                f"   🆔 {row['user_id']}\n"
                f"   👤 {username}\n"
                f"   ⭐ Lv.{row['level']} | XP {row['xp']}\n"
                f"   🎮 {row['games_played']} игр | "
                f"🏆 {row['games_won']} побед"
            )

        keyboard = [
            [
                {"text": "⬅️ Назад"}
            ]
        ]

        self.send_message(
            chat_id,
            "\n".join(lines),
            keyboard
        )

    def show_developer_games(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        with self.database.connect() as connection:

            row = connection.execute(
                """
                SELECT
                    COALESCE(SUM(games_played), 0),
                    COALESCE(SUM(games_won), 0)
                FROM users
                """
            ).fetchone()

        played = row[0]
        won = row[1]

        winrate = (
            (won / played) * 100
            if played
            else 0
        )

        self.audit(
            user_id,
            "VIEW_GAME_STATS"
        )

        keyboard = [
            [
                {"text": "⬅️ Назад"}
            ]
        ]

        self.send_message(
            chat_id,
            "🎮 GAME SYSTEM\n\n"
            f"🎮 Игр сыграно: {played}\n"
            f"🏆 Побед: {won}\n"
            f"📈 Побед: {winrate:.1f}%\n\n"
            "Доступные игры:\n"
            "🎲 Dice\n"
            "🔢 Guess Number\n"
            "🧠 Quiz\n"
            "🧩 Riddles\n"
            "⚡ Reaction",
            keyboard
        )

    def show_audit_log(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        with self.database.connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    actor_id,
                    target_id,
                    action,
                    details,
                    created_at
                FROM audit_log
                ORDER BY id DESC
                LIMIT 15
                """
            ).fetchall()

        lines = [
            "📜 T-OS AUDIT LOG",
            "",
            "Последние 15 событий:",
            ""
        ]

        if not rows:
            lines.append(
                "Audit Log пока пуст."
            )

        for row in rows:

            target = (
                f" → {row['target_id']}"
                if row["target_id"]
                else ""
            )

            details = (
                f"\n   {row['details']}"
                if row["details"]
                else ""
            )

            lines.append(
                f"🕒 {row['created_at']}\n"
                f"👤 {row['actor_id']}{target}\n"
                f"🔧 {row['action']}"
                f"{details}\n"
            )

        self.audit(
            user_id,
            "VIEW_AUDIT_LOG"
        )

        keyboard = [
            [
                {"text": "⬅️ Назад"}
            ]
        ]

        self.send_message(
            chat_id,
            "\n".join(lines),
            keyboard
        )

    def show_restrictions(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        with self.database.connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    user_id,
                    until,
                    reason
                FROM user_restrictions
                ORDER BY until ASC
                """
            ).fetchall()

        lines = [
            "🚫 USER RESTRICTIONS",
            ""
        ]

        if not rows:
            lines.append(
                "Активных ограничений нет."
            )

        for row in rows:

            lines.append(
                f"🔴 {row['user_id']}\n"
                f"До: {row['until']}\n"
                f"Причина: "
                f"{row['reason'] or 'не указана'}\n"
            )

        lines.extend([
            "",
            "Управление ограничениями будет "
            "расширено в следующей версии."
        ])

        self.audit(
            user_id,
            "VIEW_RESTRICTIONS"
        )

        keyboard = [
            [
                {"text": "⬅️ Назад"}
            ]
        ]

        self.send_message(
            chat_id,
            "\n".join(lines),
            keyboard
        )

    def show_system_info(
        self,
        chat_id,
        user_id
    ):
        if not self.is_developer(user_id):
            return

        with self.database.connect() as connection:

            tables = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()

        table_names = [
            row["name"]
            for row in tables
        ]

        self.audit(
            user_id,
            "VIEW_SYSTEM_INFO"
        )

        keyboard = [
            [
                {"text": "⬅️ Назад"}
            ]
        ]

        self.send_message(
            chat_id,
            "⚙️ T-OS SYSTEM INFO\n\n"
            "🖥️ System: T-OS\n"
            "📦 Version: 0.1\n"
            "🧠 Core: TOS-Core\n"
            "💻 Shell: T-Shell\n"
            "📁 Filesystem: TFS\n"
            "🗄️ Database: SQLite\n"
            "🌐 Platform: Telegram\n"
            "🚂 Runtime: Railway\n"
            "🟢 Status: ONLINE\n\n"
            "SQLite tables:\n"
            + "\n".join(
                f"• {name}"
                for name in table_names
            ),
            keyboard
        )

    # =========================================================
    # TELEGRAM
    # =========================================================

    def send_message(
        self,
        chat_id,
        text,
        keyboard=None
    ):
        data = {
            "chat_id": chat_id,
            "text": text
        }

        if keyboard:
            data["reply_markup"] = {
                "keyboard": keyboard,
                "resize_keyboard": True
            }

        self.bot.request(
            "sendMessage",
            data
        )

    # =========================================================
    # HOME
    # =========================================================

    def show_home(
        self,
        chat_id,
        user_id=None
    ):
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

        if (
            user_id is not None
            and self.is_developer(user_id)
        ):
            keyboard.append([
                {"text": "🛡️ Developer Panel"}
            ])

        self.send_message(
            chat_id,
            "🖥️ T-OS\n\n"
            "Добро пожаловать в операционную систему "
            "внутри Telegram.\n\n"
            "Выберите приложение:",
            keyboard
        )

    # =========================================================
    # FILE SYSTEM
    # =========================================================

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

    def show_files(
        self,
        chat_id,
        user_id
    ):
        self.initialize_filesystem(
            user_id
        )

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
                {"text": "📄 Создать файл"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            "📁 ФАЙЛЫ T-OS\n\n"
            "📍 /home/user/\n\n"
            "Выберите папку или действие:",
            keyboard
        )

    def ask_filename(
        self,
        chat_id,
        user_id
    ):
        self.file_states[user_id] = (
            "waiting_filename"
        )

        self.send_message(
            chat_id,
            "📄 Введите имя файла:\n\n"
            "Например:\n"
            "hello.txt\n"
            "notes.md\n"
            "test.py"
        )

    def create_new_file(
        self,
        chat_id,
        user_id,
        filename
    ):
        filename = filename.strip()

        if not filename:
            self.send_message(
                chat_id,
                "❌ Имя файла не может быть пустым."
            )
            return

        if "/" in filename or "\\" in filename:
            self.file_states.pop(
                user_id,
                None
            )

            self.send_message(
                chat_id,
                "❌ В имени файла нельзя использовать / или \\."
            )
            return

        if len(filename) > 100:
            self.file_states.pop(
                user_id,
                None
            )

            self.send_message(
                chat_id,
                "❌ Имя файла слишком длинное."
            )
            return

        self.initialize_filesystem(
            user_id
        )

        path = (
            f"/home/user/Documents/{filename}"
        )

        if self.database.path_exists(
            user_id,
            path
        ):
            self.file_states.pop(
                user_id,
                None
            )

            self.send_message(
                chat_id,
                f"❌ Файл {filename} уже существует."
            )
            return

        self.database.create_file(
            user_id,
            path,
            file_type="file",
            content=""
        )

        self.database.add_xp(
            user_id,
            5
        )

        if not self.database.has_achievement(
            user_id,
            "Explorer"
        ):
            self.database.unlock_achievement(
                user_id,
                "Explorer"
            )

        self.file_states.pop(
            user_id,
            None
        )

        self.send_message(
            chat_id,
            f"✅ Файл создан!\n\n"
            f"📄 {filename}\n"
            f"📍 {path}\n\n"
            "✨ +5 XP"
        )

    def show_directory(
        self,
        chat_id,
        user_id,
        directory
    ):
        self.initialize_filesystem(
            user_id
        )

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

        keyboard = []
        found = False

        for file in files:
            path = file[1]
            file_type = file[2]

            if (
                path.count("/")
                != directory.count("/") + 1
            ):
                continue

            found = True
            filename = path.split("/")[-1]

            if file_type == "directory":
                lines.append(
                    f"📂 {filename}"
                )
            else:
                lines.append(
                    f"📄 {filename}"
                )

                keyboard.append([
                    {"text": f"📄 {filename}"}
                ])

        if not found:
            lines.append(
                "Папка пуста."
            )

        keyboard.append([
            {"text": "📁 Файлы"},
            {"text": "🖥️ Главное меню"}
        ])

        self.send_message(
            chat_id,
            "\n".join(lines),
            keyboard
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

        content = file[3] or "(пусто)"
        filename = path.split("/")[-1]

        keyboard = [
            [
                {"text": "✏️ Редактировать"}
            ],
            [
                {"text": "📁 Файлы"}
            ]
        ]

        self.file_states[user_id] = (
            f"opened:{path}"
        )

        self.send_message(
            chat_id,
            f"📄 {filename}\n\n"
            f"📍 {path}\n\n"
            "Содержимое:\n"
            "────────────\n"
            f"{content}\n"
            "────────────",
            keyboard
        )

    def start_editing(
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
            self.file_states.pop(
                user_id,
                None
            )

            self.send_message(
                chat_id,
                "❌ Файл не найден."
            )
            return

        filename = path.split("/")[-1]

        self.file_states[user_id] = (
            f"editing:{path}"
        )

        self.send_message(
            chat_id,
            f"✏️ РЕДАКТИРОВАНИЕ\n\n"
            f"📄 {filename}\n"
            f"📍 {path}\n\n"
            "Отправьте новое содержимое файла.\n\n"
            "⚠️ Старое содержимое будет заменено."
        )

    def save_file_content(
        self,
        chat_id,
        user_id,
        path,
        content
    ):
        file = self.database.get_file(
            user_id,
            path
        )

        if not file:
            self.file_states.pop(
                user_id,
                None
            )

            self.send_message(
                chat_id,
                "❌ Файл больше не существует."
            )
            return

        self.database.update_file(
            user_id,
            path,
            content
        )

        self.database.add_xp(
            user_id,
            5
        )

        self.file_states.pop(
            user_id,
            None
        )

        filename = path.split("/")[-1]

        self.send_message(
            chat_id,
            f"✅ Файл сохранён!\n\n"
            f"📄 {filename}\n"
            f"📍 {path}\n\n"
            "✨ +5 XP"
        )

    # =========================================================
    # TERMINAL CORE
    # =========================================================

    def get_terminal_dir(
        self,
        user_id
    ):
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
        current_dir,
        target
    ):
        if target.startswith("/"):
            path = target
        else:
            path = (
                current_dir.rstrip("/")
                + "/"
                + target
            )

        parts = []

        for part in path.split("/"):
            if not part or part == ".":
                continue

            if part == "..":
                if parts:
                    parts.pop()

                continue

            parts.append(part)

        result = "/" + "/".join(parts)

        if result == "/":
            return "/home/user"

        return result

    def terminal_output(
        self,
        chat_id,
        text
    ):
        self.send_message(
            chat_id,
            text
        )

    def add_history(
        self,
        user_id,
        command
    ):
        if user_id not in self.command_history:
            self.command_history[user_id] = []

        self.command_history[user_id].append(
            command
        )

        self.command_history[user_id] = (
            self.command_history[user_id][-50:]
        )

    def handle_terminal(
        self,
        chat_id,
        user_id,
        text
    ):
        command_line = text.strip()

        if not command_line.startswith("$"):
            return

        command_line = command_line[1:].strip()

        if not command_line:
            self.terminal_output(
                chat_id,
                "T-OS Terminal\n\n"
                "Введите $ help"
            )
            return

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

        parts = command_line.split()

        command = parts[0].lower()
        args = parts[1:]

        current_dir = self.get_terminal_dir(
            user_id
        )

        self.initialize_filesystem(
            user_id
        )

        if command == "help":
            self.terminal_output(
                chat_id,
                "💻 T-OS TERMINAL 2.0\n\n"
                "$ help\n"
                "Показать список команд.\n\n"
                "$ pwd\n"
                "Показать текущую папку.\n\n"
                "$ ls\n"
                "Показать содержимое папки.\n\n"
                "$ cd <dir>\n"
                "Перейти в папку.\n\n"
                "$ touch <file>\n"
                "Создать файл.\n\n"
                "$ mkdir <dir>\n"
                "Создать папку.\n\n"
                "$ cat <file>\n"
                "Показать содержимое файла.\n\n"
                "$ write <file> <text>\n"
                "Записать текст в файл.\n\n"
                "$ echo <text>\n"
                "Вывести текст.\n\n"
                "$ rm <file>\n"
                "Удалить файл.\n\n"
                "$ mv <src> <dst>\n"
                "Переместить файл.\n\n"
                "$ cp <src> <dst>\n"
                "Скопировать файл.\n\n"
                "$ tree\n"
                "Показать дерево файлов.\n\n"
                "$ history\n"
                "Показать историю команд.\n\n"
                "$ whoami\n"
                "Показать текущего пользователя.\n\n"
                "$ date\n"
                "Показать дату и время.\n\n"
                "$ neofetch\n"
                "Информация о T-OS.\n\n"
                "$ clear\n"
                "Очистить экран.\n\n"
                "Все команды работают только "
                "в виртуальной файловой системе."
            )
            return

        if command == "pwd":
            self.terminal_output(
                chat_id,
                current_dir
            )
            return

        if command == "whoami":
            self.terminal_output(
                chat_id,
                f"tos-user-{user_id}"
            )
            return

        if command == "date":
            now = datetime.now()

            self.terminal_output(
                chat_id,
                now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            return

        if command == "clear":
            self.terminal_output(
                chat_id,
                "🧹 Terminal cleared."
            )
            return

        if command == "ls":

            directory = current_dir

            if args:
                directory = self.normalize_path(
                    current_dir,
                    args[0]
                )

            directory_file = self.database.get_file(
                user_id,
                directory
            )

            if not directory_file:
                self.terminal_output(
                    chat_id,
                    f"ls: нет такой папки: {directory}"
                )
                return

            if directory_file[2] != "directory":
                self.terminal_output(
                    chat_id,
                    f"ls: это не папка: {directory}"
                )
                return

            files = self.database.get_files(
                user_id,
                directory
            )

            output = []

            for file in files:
                path = file[1]
                file_type = file[2]

                if (
                    path.count("/")
                    != directory.count("/") + 1
                ):
                    continue

                filename = path.split("/")[-1]

                if file_type == "directory":
                    output.append(
                        f"📂 {filename}/"
                    )
                else:
                    output.append(
                        f"📄 {filename}"
                    )

            if not output:
                output.append(
                    "(пусто)"
                )

            self.terminal_output(
                chat_id,
                "\n".join(output)
            )
            return

        if command == "cd":

            target = (
                args[0]
                if args
                else "/home/user"
            )

            new_dir = self.normalize_path(
                current_dir,
                target
            )

            file = self.database.get_file(
                user_id,
                new_dir
            )

            if not file:
                self.terminal_output(
                    chat_id,
                    f"cd: папка не найдена: {new_dir}"
                )
                return

            if file[2] != "directory":
                self.terminal_output(
                    chat_id,
                    f"cd: это не папка: {new_dir}"
                )
                return

            self.set_terminal_dir(
                user_id,
                new_dir
            )

            self.terminal_output(
                chat_id,
                f"📍 {new_dir}"
            )
            return

        if command == "touch":

            if len(args) != 1:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ touch filename"
                )
                return

            filename = args[0]

            if "/" in filename or "\\" in filename:
                self.terminal_output(
                    chat_id,
                    "❌ Недопустимое имя файла."
                )
                return

            path = (
                current_dir.rstrip("/")
                + "/"
                + filename
            )

            if self.database.path_exists(
                user_id,
                path
            ):
                self.terminal_output(
                    chat_id,
                    "❌ Такой объект уже существует."
                )
                return

            self.database.create_file(
                user_id,
                path,
                file_type="file",
                content=""
            )

            self.database.add_xp(
                user_id,
                5
            )

            self.terminal_output(
                chat_id,
                f"✅ Создан файл: {filename}\n"
                "✨ +5 XP"
            )
            return

        if command == "mkdir":

            if len(args) != 1:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ mkdir dirname"
                )
                return

            dirname = args[0]

            if "/" in dirname or "\\" in dirname:
                self.terminal_output(
                    chat_id,
                    "❌ Недопустимое имя папки."
                )
                return

            path = (
                current_dir.rstrip("/")
                + "/"
                + dirname
            )

            if self.database.path_exists(
                user_id,
                path
            ):
                self.terminal_output(
                    chat_id,
                    "❌ Такой объект уже существует."
                )
                return

            self.database.create_file(
                user_id,
                path,
                file_type="directory"
            )

            self.database.add_xp(
                user_id,
                5
            )

            self.terminal_output(
                chat_id,
                f"✅ Создана папка: {dirname}\n"
                "✨ +5 XP"
            )
            return

        if command == "cat":

            if len(args) != 1:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ cat filename"
                )
                return

            path = self.normalize_path(
                current_dir,
                args[0]
            )

            file = self.database.get_file(
                user_id,
                path
            )

            if not file:
                self.terminal_output(
                    chat_id,
                    f"cat: файл не найден: {args[0]}"
                )
                return

            if file[2] != "file":
                self.terminal_output(
                    chat_id,
                    "cat: это папка."
                )
                return

            content = file[3] or "(пусто)"

            self.terminal_output(
                chat_id,
                content
            )
            return

        if command == "write":

            if len(args) < 2:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ write filename text"
                )
                return

            filename = args[0]
            content = " ".join(args[1:])

            path = self.normalize_path(
                current_dir,
                filename
            )

            file = self.database.get_file(
                user_id,
                path
            )

            if not file:
                self.terminal_output(
                    chat_id,
                    "❌ Файл не найден."
                )
                return

            if file[2] != "file":
                self.terminal_output(
                    chat_id,
                    "❌ Это папка."
                )
                return

            self.database.update_file(
                user_id,
                path,
                content
            )

            self.database.add_xp(
                user_id,
                5
            )

            self.terminal_output(
                chat_id,
                "✅ Файл записан.\n"
                "✨ +5 XP"
            )
            return

        if command == "echo":

            self.terminal_output(
                chat_id,
                " ".join(args)
            )
            return

        if command == "rm":

            if len(args) != 1:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ rm filename"
                )
                return

            path = self.normalize_path(
                current_dir,
                args[0]
            )

            file = self.database.get_file(
                user_id,
                path
            )

            if not file:
                self.terminal_output(
                    chat_id,
                    "❌ Объект не найден."
                )
                return

            if file[2] == "directory":
                self.terminal_output(
                    chat_id,
                    "❌ Удаление папок пока запрещено."
                )
                return

            self.database.delete_file(
                user_id,
                path
            )

            self.terminal_output(
                chat_id,
                f"🗑️ Удалён: {args[0]}"
            )
            return

        if command == "cp":

            if len(args) != 2:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ cp source destination"
                )
                return

            source = self.normalize_path(
                current_dir,
                args[0]
            )

            destination = self.normalize_path(
                current_dir,
                args[1]
            )

            source_file = self.database.get_file(
                user_id,
                source
            )

            if not source_file:
                self.terminal_output(
                    chat_id,
                    "❌ Исходный файл не найден."
                )
                return

            if source_file[2] != "file":
                self.terminal_output(
                    chat_id,
                    "❌ Копирование папок пока не поддерживается."
                )
                return

            if self.database.path_exists(
                user_id,
                destination
            ):
                self.terminal_output(
                    chat_id,
                    "❌ Файл назначения уже существует."
                )
                return

            self.database.create_file(
                user_id,
                destination,
                file_type="file",
                content=source_file[3] or ""
            )

            self.database.add_xp(
                user_id,
                5
            )

            self.terminal_output(
                chat_id,
                f"📋 Скопировано: {args[0]} → {args[1]}\n"
                "✨ +5 XP"
            )
            return

        if command == "mv":

            if len(args) != 2:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ mv source destination"
                )
                return

            source = self.normalize_path(
                current_dir,
                args[0]
            )

            destination = self.normalize_path(
                current_dir,
                args[1]
            )

            source_file = self.database.get_file(
                user_id,
                source
            )

            if not source_file:
                self.terminal_output(
                    chat_id,
                    "❌ Исходный файл не найден."
                )
                return

            if self.database.path_exists(
                user_id,
                destination
            ):
                self.terminal_output(
                    chat_id,
                    "❌ Назначение уже существует."
                )
                return

            if source_file[2] == "directory":
                self.terminal_output(
                    chat_id,
                    "❌ Перемещение папок пока не поддерживается."
                )
                return

            self.database.create_file(
                user_id,
                destination,
                file_type="file",
                content=source_file[3] or ""
            )

            self.database.delete_file(
                user_id,
                source
            )

            self.database.add_xp(
                user_id,
                5
            )

            self.terminal_output(
                chat_id,
                f"📦 Перемещено: {args[0]} → {args[1]}\n"
                "✨ +5 XP"
            )
            return

        if command == "tree":

            root = current_dir

            if args:
                root = self.normalize_path(
                    current_dir,
                    args[0]
                )

            root_file = self.database.get_file(
                user_id,
                root
            )

            if not root_file:
                self.terminal_output(
                    chat_id,
                    "❌ Путь не найден."
                )
                return

            if root_file[2] != "directory":
                self.terminal_output(
                    chat_id,
                    "❌ Это не папка."
                )
                return

            lines = [
                f"📂 {root.split('/')[-1] or '/'}"
            ]

            self.build_tree(
                user_id,
                root,
                lines,
                ""
            )

            self.terminal_output(
                chat_id,
                "\n".join(lines)
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
                    "(история пуста)"
                )
                return

            lines = []

            for index, item in enumerate(
                history,
                start=1
            ):
                lines.append(
                    f"{index:02d}  ${item}"
                )

            self.terminal_output(
                chat_id,
                "\n".join(lines)
            )
            return

        if command == "neofetch":

            self.terminal_output(
                chat_id,
                "        ████████\n"
                "      ██  T-OS  ██\n"
                "     ██          ██\n"
                "      ██  OS   ██\n"
                "        ████████\n\n"
                "🖥️ T-OS\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Version: 0.1\n"
                "Kernel: TOS-Core\n"
                "Shell: T-Shell\n"
                "Filesystem: TFS\n"
                "Database: SQLite\n"
                "Mode: Virtual\n"
                "Platform: Telegram\n"
                "Status: ONLINE 🟢"
            )
            return

        self.terminal_output(
            chat_id,
            f"❌ Команда не найдена: {command}\n\n"
            "Введите $ help"
        )

    # =========================================================
    # TREE
    # =========================================================

    def build_tree(
        self,
        user_id,
        directory,
        lines,
        prefix
    ):
        files = self.database.get_files(
            user_id,
            directory
        )

        children = []

        for file in files:
            path = file[1]

            if (
                path.count("/")
                != directory.count("/") + 1
            ):
                continue

            children.append(file)

        for index, file in enumerate(
            children
        ):
            path = file[1]
            file_type = file[2]

            is_last = (
                index == len(children) - 1
            )

            branch = (
                "└── "
                if is_last
                else "├── "
            )

            name = path.split("/")[-1]

            if file_type == "directory":

                lines.append(
                    prefix
                    + branch
                    + "📂 "
                    + name
                )

                new_prefix = (
                    prefix + "    "
                    if is_last
                    else prefix + "│   "
                )

                self.build_tree(
                    user_id,
                    path,
                    lines,
                    new_prefix
                )

            else:

                lines.append(
                    prefix
                    + branch
                    + "📄 "
                    + name
                )

    # =========================================================
    # TERMINAL APP
    # =========================================================

    def show_terminal(
        self,
        chat_id,
        user_id
    ):
        current_dir = self.get_terminal_dir(
            user_id
        )

        keyboard = [
            [
                {"text": "📁 Файлы"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            "💻 T-OS TERMINAL 2.0\n\n"
            f"user@t-os:{current_dir}$\n\n"
            "$ help\n"
            "$ ls\n"
            "$ pwd\n"
            "$ tree\n"
            "$ neofetch\n\n"
            "Введите команду сообщением.",
            keyboard
        )

    # =========================================================
    # PROFILE
    # =========================================================

    def show_profile(
        self,
        chat_id,
        message
    ):
        user_info = message.get(
            "from",
            {}
        )

        user_id = user_info.get(
            "id"
        )

        username = user_info.get(
            "username"
        )

        if username:
            username = f"@{username}"
        else:
            username = "не установлен"

        user = self.database.get_user(
            user_id
        )

        if not user:
            self.database.create_user(
                user_id,
                user_info.get("username")
            )

            user = self.database.get_user(
                user_id
            )

        keyboard = [
            [
                {"text": "🏆 Достижения"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            "👤 ПРОФИЛЬ T-OS\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Username: {username}\n\n"
            f"⭐ Уровень: {user['level']}\n"
            f"✨ XP: {user['xp']}\n"
            f"🪙 T-Coins: {user['coins']}\n\n"
            "📊 СТАТИСТИКА\n"
            f"⌨️ Команд: {user['commands']}\n"
            f"🎮 Игр сыграно: {user['games_played']}\n"
            f"🏆 Побед в играх: {user['games_won']}",
            keyboard
        )

    # =========================================================
    # ACHIEVEMENTS
    # =========================================================

    def show_achievements(
        self,
        chat_id,
        user_id
    ):
        achievements = self.database.get_achievements(
            user_id
        )

        achievement_names = {
            "First Login": "🚀 Первый вход",
            "First Game": "🎮 Первая игра",
            "100 Commands": "⌨️ 100 команд",
            "Terminal User": "💻 Пользователь Terminal",
            "Millionaire": "🪙 Миллионер",
            "Group Veteran": "👥 Ветеран группы",
            "Gift Sender": "🎁 Отправитель подарков",
            "Explorer": "🗺️ Исследователь"
        }

        lines = [
            "🏆 ДОСТИЖЕНИЯ T-OS",
            "",
            f"Разблокировано: {len(achievements)}",
            ""
        ]

        unlocked = set()

        for achievement in achievements:

            name = achievement["achievement"]

            unlocked.add(name)

            lines.append(
                "✅ "
                + achievement_names.get(
                    name,
                    name
                )
            )

        all_achievements = [
            "First Login",
            "First Game",
            "100 Commands",
            "Terminal User",
            "Millionaire",
            "Group Veteran",
            "Gift Sender",
            "Explorer"
        ]

        for name in all_achievements:

            if name not in unlocked:

                lines.append(
                    "🔒 "
                    + achievement_names.get(
                        name,
                        name
                    )
                )

        keyboard = [
            [
                {"text": "👤 Профиль"}
            ],
            [
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            "\n".join(lines),
            keyboard
        )

    # =========================================================
    # NOTES
    # =========================================================

    def show_notes(
        self,
        chat_id
    ):
        self.send_message(
            chat_id,
            "📝 ЗАМЕТКИ\n\n"
            "Система заметок T-OS находится в разработке."
        )

    # =========================================================
    # CALCULATOR
    # =========================================================

    def show_calculator(
        self,
        chat_id
    ):
        self.send_message(
            chat_id,
            "🧮 КАЛЬКУЛЯТОР\n\n"
            "Калькулятор T-OS находится в разработке."
        )

    # =========================================================
    # GAMES
    # =========================================================

    def show_games(
        self,
        chat_id,
        user_id=None
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
                {"text": "🖥️ Главное меню"}
            ]
        ]

        self.send_message(
            chat_id,
            "🎮 T-OS GAMES\n\n"
            "Выберите игру:\n\n"
            "🎲 Dice — бросок кубика\n"
            "🔢 Guess Number — угадай число\n"
            "🧠 Quiz — викторина\n"
            "🧩 Riddles — загадки\n"
            "⚡ Reaction — реакция\n\n"
            "⭐ За игры можно получать XP\n"
            "🪙 За игры можно получать T-Coins",
            keyboard
        )

    def start_dice(
        self,
        chat_id,
        user_id
    ):
        self.games.cancel_game(
            user_id
        )

        result, won = self.games.start_dice(
            user_id
        )

        if won:
            result_text = (
                "🎉 Отличный бросок!"
            )
            reward = (
                "⭐ +10 XP\n"
                "🪙 +10 T-Coins"
            )
        else:
            result_text = (
                "🙂 В этот раз не повезло."
            )
            reward = (
                "⭐ +10 XP\n"
                "🪙 +2 T-Coins"
            )

        self.send_message(
            chat_id,
            "🎲 DICE\n\n"
            f"Выпало: {result}\n\n"
            f"{result_text}\n\n"
            f"{reward}"
        )

        self.show_games(
            chat_id,
            user_id
        )

    def start_guess(
        self,
        chat_id,
        user_id
    ):
        message = self.games.start_guess(
            user_id
        )

        keyboard = [
            [
                {"text": "❌ Выйти из игры"}
            ]
        ]

        self.send_message(
            chat_id,
            message,
            keyboard
        )

    def start_quiz(
        self,
        chat_id,
        user_id
    ):
        message = self.games.start_quiz(
            user_id
        )

        keyboard = [
            [
                {"text": "❌ Выйти из игры"}
            ]
        ]

        self.send_message(
            chat_id,
            message,
            keyboard
        )

    def start_riddle(
        self,
        chat_id,
        user_id
    ):
        message = self.games.start_riddle(
            user_id
        )

        keyboard = [
            [
                {"text": "❌ Выйти из игры"}
            ]
        ]

        self.send_message(
            chat_id,
            message,
            keyboard
        )

    def start_reaction(
        self,
        chat_id,
        user_id
    ):
        message = self.games.start_reaction(
            user_id
        )

        keyboard = [
            [
                {"text": "⚡"}
            ],
            [
                {"text": "❌ Выйти из игры"}
            ]
        ]

        self.send_message(
            chat_id,
            message,
            keyboard
        )

    # =========================================================
    # SETTINGS
    # =========================================================

    def show_settings(
        self,
        chat_id
    ):
        self.send_message(
            chat_id,
            "⚙️ НАСТРОЙКИ T-OS\n\n"
            "🌐 Язык: 🇷🇺 Русский\n"
            "🔔 Уведомления: включены\n"
            "🖥️ Режим: Personal OS"
        )

    # =========================================================
    # APP STORE
    # =========================================================

    def show_app_store(
        self,
        chat_id
    ):
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