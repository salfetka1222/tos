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
                    {
                        "text": "📁 Файловая система"
                    },
                    {
                        "text": "👥 Group OS"
                    }
                ],
                [
                    {
                        "text": "🛠 Dev Panel"
                    }
                ],
                [
                    {
                        "text": "ℹ️ Помощь"
                    }
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
                    {
                        "text": "🏠 Главная"
                    }
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            (
                "ℹ️ <b>ПОМОЩЬ T-OS</b>\n\n"
                "📁 <b>Файловая система</b>\n"
                "Работа с файлами и папками.\n\n"
                "👥 <b>Group OS</b>\n"
                "Инструменты управления группой.\n\n"
                "🛠 <b>Dev Panel</b>\n"
                "Панель разработчика."
            ),
            keyboard
        )

    # =========================================================
    # UPDATE
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

        if not chat_id or not user_id:
            return

        text = message.get(
            "text",
            ""
        )

        if not isinstance(text, str):
            text = ""

        text = text.strip()

        # =====================================================
        # FILESYSTEM STATE
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
            self.filesystem.cancel(
                user_id
            )

            self.show_main_menu(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # MAIN MENU
        # =====================================================

        if text == "🏠 Главная":
            self.filesystem.cancel(
                user_id
            )

            self.show_main_menu(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # HELP
        # =====================================================

        if text == "ℹ️ Помощь":
            self.filesystem.cancel(
                user_id
            )

            self.show_help(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # FILESYSTEM
        # =====================================================

        if text == "📁 Файловая система":
            self.filesystem.cancel(
                user_id
            )

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
            self.filesystem.go_back(
                chat_id,
                user_id
            )
            return

        # =====================================================
        # EDIT FILE
        # =====================================================

        if text == "✏️ Изменить файл":
            state = self.filesystem.states.get(
                user_id,
                {}
            )

            path = state.get(
                "path"
            )

            if path:
                self.filesystem.edit_file_start(
                    chat_id,
                    user_id,
                    path
                )

            return

        # =====================================================
        # DELETE FILE
        # =====================================================

        if text == "🗑 Удалить файл":
            state = self.filesystem.states.get(
                user_id,
                {}
            )

            path = state.get(
                "path"
            )

            if path:
                self.filesystem.delete_file_start(
                    chat_id,
                    user_id,
                    path
                )

            return

        # =====================================================
        # OPEN FILE
        # =====================================================

        if text.startswith("📄 "):
            name = text[2:].strip()

            directory = (
                self.filesystem.get_current_directory(
                    user_id
                )
            )

            if directory == "/":
                path = name
            else:
                path = (
                    directory.lstrip("/")
                    + name
                )

            self.filesystem.open_path(
                chat_id,
                user_id,
                path
            )

            return

        # =====================================================
        # OPEN FOLDER
        # =====================================================

        if text.startswith("📁 "):
            name = text[2:].strip()

            directory = (
                self.filesystem.get_current_directory(
                    user_id
                )
            )

            if directory == "/":
                path = name + "/"
            else:
                path = (
                    directory.lstrip("/")
                    + name
                    + "/"
                )

            self.filesystem.open_path(
                chat_id,
                user_id,
                path
            )

            return

        # =====================================================
        # GROUP OS
        # =====================================================

        if text == "👥 Group OS":
            self.group.show_group_dashboard(
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

        if text == "⬅️ Назад в Group OS":
            self.group.show_group_dashboard(
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

        # =====================================================
        # UNKNOWN TEXT
        # =====================================================

        self.send_message(
            chat_id,
            (
                "🤔 Я не понимаю эту команду.\n\n"
                "Используйте /start, чтобы открыть "
                "главное меню."
            )
        )