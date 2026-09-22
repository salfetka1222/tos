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

        # =====================================================
        # SYSTEMS
        # =====================================================

        self.games = GamesSystem(database)

        self.developer = DeveloperSystem(
            database
        )

        self.group_os = GroupOS(
            bot,
            database
        )

        # =====================================================
        # HANDLERS
        # =====================================================

        self.group = GroupHandler(
            bot,
            database,
            self.group_os
        )

        self.dev = DeveloperHandler(
            bot,
            database,
            self.developer
        )

        self.filesystem = FilesystemHandler(
            bot,
            database
        )

        # =====================================================
        # OLD STATES
        # =====================================================

        self.file_states = {}

        self.terminal_dirs = {}

        self.command_history = {}

    # =========================================================
    # TELEGRAM
    # =========================================================

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

    # =========================================================
    # MAIN MENU
    # =========================================================

    def show_main_menu(
        self,
        chat_id,
        user_id
    ):
        keyboard = {
            "keyboard": [
                [
                    {"text": "📁 Файловая система"},
                    {"text": "👥 Group OS"}
                ],
                [
                    {"text": "🎮 Игры"},
                    {"text": "🛠 Dev Panel"}
                ],
                [
                    {"text": "ℹ️ Помощь"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            (
                "🖥 <b>T-OS</b>\n\n"
                "Добро пожаловать в виртуальную "
                "операционную систему.\n\n"
                "Выберите нужный раздел:"
            ),
            keyboard
        )

    # =========================================================
    # HELP
    # =========================================================

    def show_help(
        self,
        chat_id,
        user_id
    ):
        keyboard = {
            "keyboard": [
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            (
                "ℹ️ <b>ПОМОЩЬ T-OS</b>\n\n"
                "📁 Файловая система — работа с файлами "
                "и папками.\n\n"
                "👥 Group OS — управление группой.\n\n"
                "🎮 Игры — игровые функции T-OS.\n\n"
                "🛠 Dev Panel — панель разработчика."
            ),
            keyboard
        )

    # =========================================================
    # UPDATE HANDLER
    # =========================================================

    def handle_update(
        self,
        update
    ):
        if not update:
            return

        message = update.get(
            "message"
        )

        if not message:
            return

        chat = message.get(
            "chat",
            {}
        )

        user = message.get(
            "from",
            {}
        )

        chat_id = chat.get(
            "id"
        )

        user_id = user.get(
            "id"
        )

        text = message.get(
            "text",
            ""
        )

        if not chat_id or not user_id:
            return

        text = text.strip()

        # =====================================================
        # FILESYSTEM STATE INPUT
        # =====================================================

        if self.filesystem.handle_state_input(
            chat_id,
            user_id,
            text
        ):
            return

        # =====================================================
        # START
        # =====================================================

        if text == "/start":
            self.show_main_menu(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # MAIN MENU
        # =====================================================

        if text == "🏠 Главная":
            self.show_main_menu(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # HELP
        # =====================================================

        if text == "ℹ️ Помощь":
            self.show_help(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # FILESYSTEM
        # =====================================================

        if text == "📁 Файловая система":
            self.filesystem.show_filesystem(
                chat_id,
                user_id
            )
            return

        if text == "📂 Мои файлы":
            self.filesystem.show_files(
                chat_id,
                user_id
            )
            return

        if text == "📄 Создать файл":
            self.filesystem.create_file_start(
                chat_id,
                user_id
            )
            return

        if text == "📁 Создать папку":
            self.filesystem.create_folder_start(
                chat_id,
                user_id
            )
            return

        if text == "🔄 Обновить":
            self.filesystem.show_files(
                chat_id,
                user_id
            )
            return

        if text == "⬅️ Назад":
            self.filesystem.show_files(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # GROUP OS
        # =====================================================

        if text == "👥 Group OS":
            self.group.show_dashboard(
                chat_id,
                user_id
            )
            return

        if text == "👥 Участники":
            self.group.show_members(
                chat_id,
                user_id
            )
            return

        if text == "🛡 Модерация":
            self.group.show_moderation(
                chat_id,
                user_id
            )
            return

        if text == "📜 Журнал группы":
            self.group.show_audit_log(
                chat_id,
                user_id
            )
            return

        if text == "⚙️ Права доступа":
            self.group.show_permissions(
                chat_id,
                user_id
            )
            return

        if text == "🤖 Настройки ИИ":
            self.group.show_ai_settings(
                chat_id,
                user_id
            )
            return

        if text == "📊 Статистика группы":
            self.group.show_statistics(
                chat_id,
                user_id
            )
            return

        if text == "🔄 Обновить":
            self.group.show_dashboard(
                chat_id,
                user_id
            )
            return

        if text == "🖥️ Главное меню":
            self.show_main_menu(
                chat_id,
                user_id
            )
            return

        if text == "⬅️ Назад в Group OS":
            self.group.show_dashboard(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # DEVELOPER PANEL
        # =====================================================

        if text == "/dev":
            self.dev.show_panel(
                chat_id,
                user_id
            )
            return

        if text == "🛠 Dev Panel":
            self.dev.show_panel(
                chat_id,
                user_id
            )
            return

        if text == "📊 Статистика":
            self.dev.show_statistics(
                chat_id,
                user_id
            )
            return

        if text == "👥 Пользователи":
            self.dev.show_users(
                chat_id,
                user_id
            )
            return

        if text == "📜 Audit Log":
            self.dev.show_audit_log(
                chat_id,
                user_id
            )
            return

        if text == "🗄 Database":
            self.dev.show_database(
                chat_id,
                user_id
            )
            return

        if text == "🖥 System":
            self.dev.show_system(
                chat_id,
                user_id
            )
            return

        if text == "⬅️ Developer Panel":
            self.dev.show_panel(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # GAMES
        # =====================================================

        if text == "🎮 Игры":
            try:
                keyboard = {
                    "keyboard": [
                        [
                            {"text": "🎲 Бросить кубик"}
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
                        "🎮 <b>ИГРЫ</b>\n\n"
                        "Выберите игру:"
                    ),
                    keyboard
                )

            except Exception:
                self.send_message(
                    chat_id,
                    "❌ Не удалось открыть игры."
                )

            return

        # =====================================================
        # UNKNOWN COMMAND
        # =====================================================

        if text.startswith("/"):
            self.send_message(
                chat_id,
                (
                    "❌ Неизвестная команда.\n\n"
                    "Используйте /start для открытия "
                    "главного меню."
                )
            )
            return