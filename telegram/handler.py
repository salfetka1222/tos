from telegram.bot import TelegramBot
from core.dev import DeveloperSystem
from core.group_os import GroupOS

from telegram.handlers.group import GroupHandler
from telegram.handlers.developer import DeveloperHandler
from telegram.handlers.filesystem import FilesystemHandler
from telegram.handlers.terminal import TerminalHandler
from telegram.handlers.profile import ProfileHandler


class TelegramHandler:

    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

        self.developer = DeveloperSystem(database)
        self.group_os = GroupOS(bot, database)

        self.filesystem = FilesystemHandler(
            bot,
            database
        )

        self.terminal = TerminalHandler(
            bot,
            database,
            self.filesystem
        )

        self.profile = ProfileHandler(
            bot,
            database
        )

        self.group = GroupHandler(
            bot,
            database,
            self.group_os
        )

        self.dev_panel = DeveloperHandler(
            bot,
            database,
            self.developer
        )

    # =========================
    # TELEGRAM
    # =========================

    def send_message(self, chat_id, text, reply_markup=None):
        data = {
            "chat_id": chat_id,
            "text": text
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

    # =========================
    # MAIN MENU
    # =========================

    def main_menu(self, chat_id):
        keyboard = {
            "keyboard": [
                [
                    {"text": "👤 Мой профиль"},
                    {"text": "📁 Файловая система"}
                ],
                [
                    {"text": "💻 Terminal"},
                    {"text": "👥 Group OS"}
                ],
                [
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
                "🖥️ <b>T-OS</b>\n\n"
                "Добро пожаловать в T-OS.\n\n"
                "Выберите нужный раздел:"
            ),
            keyboard
        )

    # =========================
    # HELP
    # =========================

    def show_help(self, chat_id):
        self.send_message(
            chat_id,
            (
                "ℹ️ <b>T-OS HELP</b>\n\n"

                "👤 <b>Мой профиль</b>\n"
                "Профиль, XP, уровень, монеты и статистика.\n\n"

                "📁 <b>Файловая система</b>\n"
                "Создание и управление файлами и папками.\n\n"

                "💻 <b>Terminal</b>\n"
                "Виртуальный терминал T-OS.\n\n"

                "👥 <b>Group OS</b>\n"
                "Инструменты управления группами.\n\n"

                "🛠 <b>Dev Panel</b>\n"
                "Панель разработчика.\n\n"

                "Команда:\n"
                "<code>/start</code> — главное меню\n"
                "<code>/help</code> — помощь"
            )
        )

    # =========================
    # UPDATE
    # =========================

    def handle_update(self, update):
        if not update:
            return

        message = update.get("message")

        if not message:
            return

        chat = message.get("chat", {})
        user = message.get("from", {})

        chat_id = chat.get("id")
        user_id = user.get("id")

        if not chat_id or not user_id:
            return

        text = message.get("text", "")

        if not text:
            return

        text = text.strip()

        username = user.get("username")

        # =========================
        # REGISTER USER
        # =========================

        try:
            self.database.create_user(
                user_id,
                username
            )
        except Exception:
            pass

        # =========================
        # COMMAND COUNTER
        # =========================

        if text.startswith("/"):
            try:
                self.database.increment_commands(
                    user_id
                )
            except Exception:
                pass

        # =========================
        # TERMINAL COMMANDS
        # =========================

        try:
            if self.terminal.handle_command(
                chat_id,
                user_id,
                text
            ):
                return
        except Exception:
            pass

        # =========================
        # FILESYSTEM STATE
        # =========================

        try:
            if self.filesystem.handle_input(
                chat_id,
                user_id,
                text
            ):
                return
        except Exception:
            pass

        # =========================
        # START
        # =========================

        if text == "/start":
            try:
                self.filesystem.cancel(user_id)
            except Exception:
                pass

            self.main_menu(chat_id)
            return

        # =========================
        # HELP
        # =========================

        if text == "/help":
            self.show_help(chat_id)
            return

        if text == "ℹ️ Помощь":
            self.show_help(chat_id)
            return

        # =========================
        # NEW
        # =========================

        if text == "/new":
            try:
                self.filesystem.cancel(user_id)
            except Exception:
                pass

            self.main_menu(chat_id)
            return

        # =========================
        # PROFILE
        # =========================

        if text == "👤 Мой профиль":
            self.profile.show_profile(
                chat_id,
                user_id
            )
            return

        if text == "🏆 Достижения":
            self.profile.show_achievements(
                chat_id,
                user_id
            )
            return

        if text == "🔄 Обновить профиль":
            self.profile.show_profile(
                chat_id,
                user_id
            )
            return

        # =========================
        # FILESYSTEM
        # =========================

        if text == "📁 Файловая система":
            self.filesystem.show_filesystem(
                chat_id,
                user_id
            )
            return

        # =========================
        # TERMINAL
        # =========================

        if text == "💻 Terminal":
            self.terminal.show_terminal(
                chat_id,
                user_id
            )
            return

        if text == "📂 ls":
            self.terminal.command_ls(
                chat_id,
                user_id
            )
            return

        if text == "📍 pwd":
            self.terminal.command_pwd(
                chat_id,
                user_id
            )
            return

        if text == "📁 mkdir":
            self.send_message(
                chat_id,
                (
                    "📁 <b>MKDIR</b>\n\n"
                    "Введите имя папки:\n\n"
                    "<code>documents</code>"
                )
            )
            return

        if text == "📄 touch":
            self.send_message(
                chat_id,
                (
                    "📄 <b>TOUCH</b>\n\n"
                    "Введите имя файла:\n\n"
                    "<code>example.txt</code>"
                )
            )
            return

        if text == "🧹 clear":
            self.terminal.command_clear(
                chat_id,
                user_id
            )
            return

        # =========================
        # GROUP OS
        # =========================

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

        # =========================
        # DEV PANEL
        # =========================

        if text == "🛠 Dev Panel":
            self.dev_panel.show_panel(
                chat_id,
                user_id
            )
            return

        if text == "📊 Статистика":
            self.dev_panel.show_statistics(
                chat_id,
                user_id
            )
            return

        if text == "👥 Пользователи":
            self.dev_panel.show_users(
                chat_id,
                user_id
            )
            return

        if text == "📜 Audit Log":
            self.dev_panel.show_audit_log(
                chat_id,
                user_id
            )
            return

        if text == "🗄 Database":
            self.dev_panel.show_database(
                chat_id,
                user_id
            )
            return

        if text == "🖥 System":
            self.dev_panel.show_system(
                chat_id,
                user_id
            )
            return

        if text == "🏠 Главная":
            self.main_menu(chat_id)
            return

        if text == "🖥️ Главное меню":
            self.main_menu(chat_id)
            return

        # =========================
        # UNKNOWN
        # =========================

        self.send_message(
            chat_id,
            (
                "❓ Неизвестная команда.\n\n"
                "Используйте меню T-OS или "
                "<code>/help</code>."
            )
        )