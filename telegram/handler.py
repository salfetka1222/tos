from telegram.handlers.group import GroupHandler
from telegram.handlers.developer import DeveloperHandler
from telegram.handlers.filesystem import FilesystemHandler
from telegram.handlers.terminal import TerminalHandler
from telegram.handlers.profile import ProfileHandler
from telegram.handlers.achievements import AchievementsHandler

from core.dev import DeveloperSystem
from core.group_os import GroupOS


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

        self.achievements = AchievementsHandler(
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
                    {"text": "🏆 Достижения"}
                ],
                [
                    {"text": "📁 Файловая система"},
                    {"text": "💻 Terminal"}
                ],
                [
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
                "Профиль, XP, уровень и монеты.\n\n"

                "🏆 <b>Достижения</b>\n"
                "Ваш прогресс и награды.\n\n"

                "📁 <b>Файловая система</b>\n"
                "Создание и управление файлами.\n\n"

                "💻 <b>Terminal</b>\n"
                "Виртуальный терминал T-OS.\n\n"

                "👥 <b>Group OS</b>\n"
                "Инструменты управления группами.\n\n"

                "🛠 <b>Dev Panel</b>\n"
                "Панель разработчика.\n\n"

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
        # FIRST START
        # =========================

        if text == "/start":

            try:
                self.achievements.unlock(
                    chat_id,
                    user_id,
                    "first_start"
                )
            except Exception:
                pass

            self.main_menu(chat_id)
            return

        # =========================
        # TERMINAL
        # =========================

        try:
            if self.terminal.handle_command(
                chat_id,
                user_id,
                text
            ):
                try:
                    self.achievements.unlock(
                        chat_id,
                        user_id,
                        "first_terminal"
                    )
                except Exception:
                    pass

                return

        except Exception:
            pass

        # =========================
        # FILESYSTEM STATE
        # =========================

        try:
            # Получаем список файлов ДО действия
            before_files = []

            try:
                before_files = self.database.get_all_files(
                    user_id
                )
            except Exception:
                before_files = []

            before_file_count = 0

            for file in before_files:
                try:
                    if file["file_type"] == "file":
                        before_file_count += 1
                except Exception:
                    pass

            # Передаём сообщение файловой системе
            filesystem_handled = self.filesystem.handle_input(
                chat_id,
                user_id,
                text
            )

            if filesystem_handled:

                # Получаем список файлов ПОСЛЕ действия
                after_files = []

                try:
                    after_files = self.database.get_all_files(
                        user_id
                    )
                except Exception:
                    after_files = []

                after_file_count = 0

                for file in after_files:
                    try:
                        if file["file_type"] == "file":
                            after_file_count += 1
                    except Exception:
                        pass

                # Если появился новый файл,
                # выдаём достижение
                if after_file_count > before_file_count:

                    try:
                        self.achievements.unlock(
                            chat_id,
                            user_id,
                            "first_file"
                        )
                    except Exception:
                        pass

                return

        except Exception:
            pass

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

        # =========================
        # ACHIEVEMENTS
        # =========================

        if text == "🏆 Достижения":
            self.achievements.show_achievements(
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
        # TERMINAL MENU
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

        # =========================
        # MAIN MENU
        # =========================

        if text in (
            "🏠 Главная",
            "🖥️ Главное меню"
        ):
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