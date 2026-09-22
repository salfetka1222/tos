from datetime import datetime

from telegram.bot import TelegramBot

from games import GamesSystem
from core.dev import DeveloperSystem
from core.group_os import GroupOS


class TelegramHandler:

    def __init__(self, bot: TelegramBot, database):
        self.bot = bot
        self.database = database

        self.games = GamesSystem(database)
        self.developer = DeveloperSystem(database)
        self.group_os = GroupOS(bot, database)

        self.file_states = {}
        self.terminal_dirs = {}
        self.command_history = {}

    # =========================================================
    # BASIC
    # =========================================================

    def send_message(self, chat_id, text, reply_markup=None):
        data = {
            "chat_id": chat_id,
            "text": text
        }

        if reply_markup:
            data["reply_markup"] = reply_markup

        return self.bot.request("sendMessage", data)

    def audit(self, actor_id, action, target_id=None, details=""):
        try:
            self.database.add_audit_log(
                actor_id=actor_id,
                action=action,
                target_id=target_id,
                details=details
            )
        except Exception:
            pass

    def html_escape(self, text):
        if text is None:
            return ""

        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def handle_update(self, update):
        try:
            message = update.get("message")

            if not message:
                return

            chat = message.get("chat", {})
            user = message.get("from", {})

            chat_id = chat.get("id")
            user_id = user.get("id")

            if chat_id is None or user_id is None:
                return

            text = message.get("text", "")
            if text is None:
                text = ""

            username = user.get("username")
            first_name = user.get("first_name", "User")

            # -------------------------------------------------
            # USER
            # -------------------------------------------------

            try:
                self.database.create_user(
                    user_id=user_id,
                    username=username,
                    first_name=first_name
                )
            except Exception:
                try:
                    self.database.create_user(
                        user_id=user_id,
                        username=username
                    )
                except Exception:
                    pass

            # First Login
            try:
                if not self.database.has_achievement(user_id, "first_login"):
                    self.database.unlock_achievement(
                        user_id,
                        "first_login"
                    )
            except Exception:
                pass

            # -------------------------------------------------
            # GROUP STATISTICS
            # -------------------------------------------------

            chat_type = chat.get("type")

            if chat_type in ("group", "supergroup"):
                try:
                    self.group_os.ensure_group(chat_id)
                    self.group_os.increment_stat(
                        chat_id,
                        "messages"
                    )
                except Exception:
                    pass

            # -------------------------------------------------
            # ACTIVE GAME
            # -------------------------------------------------

            try:
                if self.games.handle_input(chat_id, user_id, text):
                    return
            except Exception:
                pass

            # -------------------------------------------------
            # FILE INPUT
            # -------------------------------------------------

            if chat_id in self.file_states:
                if self.handle_file_input(chat_id, user_id, text):
                    return

            # -------------------------------------------------
            # TERMINAL
            # -------------------------------------------------

            if text.startswith("$"):
                self.handle_terminal(chat_id, user_id, text)
                return

            # =================================================
            # COMMANDS
            # =================================================

            if text == "/start":
                self.start(chat_id, user_id)
                return

            if text == "/new":
                self.new_dialog(chat_id, user_id)
                return

            if text == "/profile":
                self.show_profile(chat_id, user_id)
                return

            if text == "/achievements":
                self.show_achievements(chat_id, user_id)
                return

            if text == "/group":
                self.show_group_dashboard(chat_id, user_id)
                return

            if text == "/dev":
                self.show_developer(chat_id, user_id)
                return

            # =================================================
            # GROUP OS
            # =================================================

            if text == "👥 Участники":
                self.show_group_members(chat_id, user_id)
                return

            if text == "🛡 Модерация":
                self.show_group_moderation(chat_id, user_id)
                return

            if text == "📜 Журнал группы":
                self.show_group_audit_log(chat_id, user_id)
                return

            if text == "⚙️ Права доступа":
                self.show_group_permissions(chat_id, user_id)
                return

            if text == "🤖 Настройки ИИ":
                self.show_group_ai_settings(chat_id, user_id)
                return

            if text == "📊 Статистика группы":
                self.show_group_statistics(chat_id, user_id)
                return

            if text == "🟢 ИИ включён":
                self.toggle_group_ai(chat_id, user_id)
                return

            if text == "🔴 ИИ выключен":
                self.toggle_group_ai(chat_id, user_id)
                return

            if text == "🔄 Обновить":
                self.show_group_dashboard(chat_id, user_id)
                return

            if text == "⬅️ Назад в Group OS":
                self.show_group_dashboard(chat_id, user_id)
                return

            # =================================================
            # MAIN MENU
            # =================================================

            if text == "🖥️ Главное меню":
                self.show_main_menu(chat_id, user_id)
                return

            if text == "📁 Файлы":
                self.show_files(chat_id, user_id)
                return

            if text == "📝 Заметки":
                self.show_notes(chat_id, user_id)
                return

            if text == "💻 Терминал":
                self.show_terminal(chat_id, user_id)
                return

            if text == "🧮 Калькулятор":
                self.show_calculator(chat_id, user_id)
                return

            if text == "🎮 Игры":
                self.show_games(chat_id, user_id)
                return

            if text == "⚙️ Настройки":
                self.show_settings(chat_id, user_id)
                return

            if text == "👤 Профиль":
                self.show_profile(chat_id, user_id)
                return

            if text == "🏆 Достижения":
                self.show_achievements(chat_id, user_id)
                return

            if text == "🛒 App Store":
                self.show_app_store(chat_id, user_id)
                return

            if text == "🛠 Developer Panel":
                self.show_developer(chat_id, user_id)
                return

            if text == "📊 Статистика":
                self.show_developer_stats(chat_id, user_id)
                return

            if text == "👥 Пользователи":
                self.show_developer_users(chat_id, user_id)
                return

            if text == "🗄 База данных":
                self.show_database_info(chat_id, user_id)
                return

            if text == "📜 Audit Log":
                self.show_audit_log(chat_id, user_id)
                return

            if text == "🖥 Система":
                self.show_system_info(chat_id, user_id)
                return

            if text == "🧪 Experimental Lab":
                self.show_experimental_lab(chat_id, user_id)
                return

            # =================================================
            # FILES
            # =================================================

            if text == "📄 Создать файл":
                self.create_file_start(chat_id, user_id)
                return

            if text == "📂 Мои файлы":
                self.show_files(chat_id, user_id)
                return

            if text == "⬅️ Назад":
                self.show_main_menu(chat_id, user_id)
                return

            # =================================================
            # GAMES
            # =================================================

            if text == "🎲 Кубик":
                self.start_dice(chat_id, user_id)
                return

            if text == "🔢 Угадай число":
                self.start_guess(chat_id, user_id)
                return

            if text == "🧠 Викторина":
                self.start_quiz(chat_id, user_id)
                return

            if text == "🧩 Загадка":
                self.start_riddle(chat_id, user_id)
                return

            if text == "⚡ Реакция":
                self.start_reaction(chat_id, user_id)
                return

            # =================================================
            # DEVELOPER PANEL
            # =================================================

            if text == "📊 Статистика":
                self.show_developer_stats(chat_id, user_id)
                return

            # =================================================
            # FALLBACK
            # =================================================

            self.send_message(
                chat_id,
                "🤖 <b>T-OS</b>\n\n"
                "Команда не распознана.\n"
                "Открой главное меню с помощью /start.",
            )

        except Exception as e:
            print(f"[HANDLER ERROR] {e}")

            try:
                self.send_message(
                    chat_id,
                    "⚠️ <b>T-OS</b>\n\n"
                    "Произошла внутренняя ошибка."
                )
            except Exception:
                pass

    # =========================================================
    # START / MENU
    # =========================================================

    def start(self, chat_id, user_id):
        self.file_states.pop(chat_id, None)
        self.terminal_dirs.pop(chat_id, None)

        self.audit(
            user_id,
            "start",
            details="T-OS started"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "📁 Файлы"},
                    {"text": "💻 Терминал"}
                ],
                [
                    {"text": "🎮 Игры"},
                    {"text": "🧮 Калькулятор"}
                ],
                [
                    {"text": "📝 Заметки"},
                    {"text": "⚙️ Настройки"}
                ],
                [
                    {"text": "👤 Профиль"},
                    {"text": "🏆 Достижения"}
                ],
                [
                    {"text": "🛒 App Store"},
                    {"text": "🛠 Developer Panel"}
                ],
                [
                    {"text": "🖥️ Главное меню"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            "🖥️ <b>T-OS</b>\n\n"
            "Добро пожаловать в виртуальную операционную систему.\n\n"
            "Выберите нужный раздел:",
            keyboard
        )

    def new_dialog(self, chat_id, user_id):
        self.file_states.pop(chat_id, None)
        self.terminal_dirs.pop(chat_id, None)

        self.send_message(
            chat_id,
            "🔄 <b>Новый диалог</b>\n\n"
            "Контекст текущего диалога очищен."
        )

        self.start(chat_id, user_id)

    def show_main_menu(self, chat_id, user_id):
        self.start(chat_id, user_id)

    # =========================================================
    # PROFILE
    # =========================================================

    def show_profile(self, chat_id, user_id):
        try:
            user = self.database.get_user(user_id)

            if not user:
                self.send_message(
                    chat_id,
                    "❌ Пользователь не найден."
                )
                return

            username = user.get("username") or "нет"
            first_name = user.get("first_name") or "User"

            text = (
                "👤 <b>ПРОФИЛЬ</b>\n\n"
                f"🧑 <b>Имя:</b> "
                f"{self.html_escape(first_name)}\n"
                f"🔗 <b>Username:</b> "
                f"@{self.html_escape(username) if username != 'нет' else 'нет'}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            )

            if "xp" in user:
                text += f"⭐ <b>XP:</b> {user['xp']}\n"

            if "commands" in user:
                text += f"⌨️ <b>Команд:</b> {user['commands']}\n"

            self.send_message(chat_id, text)

        except Exception as e:
            self.send_message(
                chat_id,
                f"⚠️ Не удалось загрузить профиль."
            )

    # =========================================================
    # ACHIEVEMENTS
    # =========================================================

    def show_achievements(self, chat_id, user_id):
        try:
            achievements = self.database.get_achievements(user_id)

            text = "🏆 <b>ДОСТИЖЕНИЯ</b>\n\n"

            if not achievements:
                text += "Пока нет полученных достижений."
            else:
                for achievement in achievements:
                    if isinstance(achievement, dict):
                        name = achievement.get(
                            "name",
                            achievement.get("title", "Achievement")
                        )
                        description = achievement.get(
                            "description",
                            ""
                        )

                        text += f"🏆 <b>{name}</b>\n"

                        if description:
                            text += f"{description}\n"

                        text += "\n"
                    else:
                        text += f"🏆 {achievement}\n"

            self.send_message(chat_id, text)

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось загрузить достижения."
            )

    # =========================================================
    # FILES
    # =========================================================

    def show_files(self, chat_id, user_id):
        try:
            files = self.database.get_files(user_id)

            keyboard = {
                "keyboard": [
                    [
                        {"text": "📄 Создать файл"},
                        {"text": "🔄 Обновить"}
                    ],
                    [
                        {"text": "🖥️ Главное меню"}
                    ]
                ],
                "resize_keyboard": True
            }

            text = "📁 <b>ФАЙЛЫ</b>\n\n"

            if not files:
                text += "Файлов пока нет."
            else:
                for file in files:
                    if isinstance(file, dict):
                        name = file.get("name", "unknown")
                        path = file.get("path", name)
                        text += f"📄 <code>{path}</code>\n"
                    else:
                        text += f"📄 <code>{file}</code>\n"

            self.send_message(
                chat_id,
                text,
                keyboard
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось открыть файловую систему."
            )

    def create_file_start(self, chat_id, user_id):
        self.file_states[chat_id] = {
            "action": "create",
            "user_id": user_id
        }

        self.send_message(
            chat_id,
            "📄 <b>Создание файла</b>\n\n"
            "Отправь путь и имя файла.\n\n"
            "Пример:\n"
            "<code>/home/readme.txt</code>\n\n"
            "Для отмены отправь:\n"
            "<code>cancel</code>"
        )

    def handle_file_input(self, chat_id, user_id, text):
        state = self.file_states.get(chat_id)

        if not state:
            return False

        if text.lower() == "cancel":
            self.file_states.pop(chat_id, None)

            self.send_message(
                chat_id,
                "❌ Операция отменена."
            )

            return True

        if state.get("action") == "create":
            path = text.strip()

            if not path:
                self.send_message(
                    chat_id,
                    "⚠️ Укажи путь к файлу."
                )
                return True

            try:
                self.database.create_file(
                    user_id=user_id,
                    path=path,
                    content=""
                )

                self.file_states.pop(chat_id, None)

                self.audit(
                    user_id,
                    "file_create",
                    details=path
                )

                self.send_message(
                    chat_id,
                    "✅ <b>Файл создан</b>\n\n"
                    f"📄 <code>{self.html_escape(path)}</code>"
                )

            except Exception as e:
                self.send_message(
                    chat_id,
                    "⚠️ Не удалось создать файл."
                )

            return True

        return False

    # =========================================================
    # TERMINAL
    # =========================================================

    def show_terminal(self, chat_id, user_id):
        current = self.terminal_dirs.get(
            chat_id,
            "/"
        )

        self.send_message(
            chat_id,
            "💻 <b>T-OS TERMINAL</b>\n\n"
            f"📁 Текущий каталог: <code>{current}</code>\n\n"
            "Команды вводятся через <code>$</code>.\n\n"
            "<code>$ help</code>\n"
            "<code>$ ls</code>\n"
            "<code>$ pwd</code>\n"
            "<code>$ cd /</code>\n"
            "<code>$ clear</code>"
        )

    def handle_terminal(self, chat_id, user_id, text):
        command = text[1:].strip()

        if not command:
            return

        self.command_history.setdefault(
            chat_id,
            []
        ).append(command)

        try:
            self.database.increment_commands(user_id)
        except Exception:
            pass

        parts = command.split()
        cmd = parts[0].lower()

        current_dir = self.terminal_dirs.get(
            chat_id,
            "/"
        )

        if cmd == "help":
            output = (
                "T-OS Terminal\n\n"
                "help   — список команд\n"
                "ls     — список файлов\n"
                "pwd    — текущий каталог\n"
                "cd     — перейти в каталог\n"
                "clear  — очистить экран"
            )

        elif cmd == "pwd":
            output = current_dir

        elif cmd == "clear":
            output = "Экран терминала очищен."

        elif cmd == "ls":
            try:
                files = self.database.get_files(user_id)

                if not files:
                    output = "Каталог пуст."

                else:
                    result = []

                    for file in files:
                        if isinstance(file, dict):
                            result.append(
                                str(
                                    file.get(
                                        "path",
                                        file.get(
                                            "name",
                                            "unknown"
                                        )
                                    )
                                )
                            )
                        else:
                            result.append(str(file))

                    output = "\n".join(result)

            except Exception:
                output = "Ошибка чтения каталога."

        elif cmd == "cd":
            if len(parts) < 2:
                output = "Использование: $ cd /path"

            else:
                new_dir = parts[1]

                if not new_dir.startswith("/"):
                    if current_dir == "/":
                        new_dir = "/" + new_dir
                    else:
                        new_dir = (
                            current_dir.rstrip("/")
                            + "/"
                            + new_dir
                        )

                self.terminal_dirs[chat_id] = new_dir
                output = f"Перешёл в {new_dir}"

        else:
            output = (
                f"Команда <code>{self.html_escape(cmd)}</code> "
                "неизвестна.\n\n"
                "Используй <code>$ help</code>."
            )

        self.send_message(
            chat_id,
            "💻 <b>Terminal</b>\n\n"
            f"<pre>{self.html_escape(output)}</pre>"
        )

    # =========================================================
    # NOTES
    # =========================================================

    def show_notes(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "📝 <b>ЗАМЕТКИ</b>\n\n"
            "Модуль заметок пока находится в разработке."
        )

    # =========================================================
    # CALCULATOR
    # =========================================================

    def show_calculator(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "🧮 <b>КАЛЬКУЛЯТОР</b>\n\n"
            "Модуль калькулятора находится в разработке."
        )

    # =========================================================
    # SETTINGS
    # =========================================================

    def show_settings(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "⚙️ <b>НАСТРОЙКИ</b>\n\n"
            "Модуль настроек T-OS находится в разработке."
        )

    # =========================================================
    # APP STORE
    # =========================================================

    def show_app_store(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "🛒 <b>T-OS APP STORE</b>\n\n"
            "Каталог приложений находится в разработке."
        )

    # =========================================================
    # GROUP OS
    # =========================================================

    def get_group_chat(self, chat_id):
        try:
            result = self.bot.request(
                "getChat",
                {
                    "chat_id": chat_id
                }
            )

            if result and result.get("ok"):
                return result.get("result", {})

        except Exception:
            pass

        return None

    def is_group(self, chat):
        if not chat:
            return False

        return chat.get("type") in (
            "group",
            "supergroup"
        )

    def get_group_member(self, chat_id, user_id):
        try:
            result = self.bot.request(
                "getChatMember",
                {
                    "chat_id": chat_id,
                    "user_id": user_id
                }
            )

            if result and result.get("ok"):
                return result.get("result", {})

        except Exception:
            pass

        return None

    def is_group_admin(self, chat_id, user_id):
        member = self.get_group_member(
            chat_id,
            user_id
        )

        if not member:
            return False

        return member.get("status") in (
            "administrator",
            "creator"
        )

    def get_bot_member(self, chat_id):
        try:
            me = self.bot.request(
                "getMe",
                {}
            )

            if not me or not me.get("ok"):
                return None

            bot_id = me["result"]["id"]

            return self.get_group_member(
                chat_id,
                bot_id
            )

        except Exception:
            return None

    def show_group_dashboard(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ <b>Group OS</b>\n\n"
                "Этот раздел работает только внутри группы."
            )
            return

        try:
            self.group_os.ensure_group(chat_id)
        except Exception:
            pass

        title = chat.get("title", "Без названия")
        username = chat.get("username")

        member_count = "—"

        try:
            member_count = self.group_os.get_member_count(
                chat_id
            )
        except Exception:
            pass

        chat_type = self.translate_chat_type(
            chat.get("type")
        )

        try:
            self.group_os.audit(
                chat_id,
                user_id,
                "group_dashboard",
                "Открыта панель Group OS"
            )
        except Exception:
            pass

        keyboard = {
            "keyboard": [
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
            ],
            "resize_keyboard": True
        }

        text = (
            "🖥️ <b>T-OS GROUP OS</b>\n\n"
            "🏠 <b>GROUP DASHBOARD</b>\n\n"
            f"📌 <b>Название:</b> "
            f"{self.html_escape(title)}\n"
            f"🆔 <b>ID:</b> "
            f"<code>{chat_id}</code>\n"
            f"💬 <b>Тип:</b> {chat_type}\n"
            f"🔗 <b>Username:</b> "
            f"{('@' + username) if username else 'нет'}\n"
            f"👥 <b>Участников:</b> {member_count}\n\n"
            "🟢 <b>T-OS:</b> ACTIVE\n\n"
            "⚙️ <b>GROUP OS MODULES</b>\n"
            "├ 👥 Members\n"
            "├ 🛡 Moderation\n"
            "├ 📜 Group Audit Log\n"
            "├ ⚙️ Permissions\n"
            "├ 🤖 AI Settings\n"
            "└ 📊 Statistics"
        )

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def translate_chat_type(self, chat_type):
        values = {
            "private": "личный чат",
            "group": "группа",
            "supergroup": "супергруппа",
            "channel": "канал"
        }

        return values.get(
            chat_type,
            str(chat_type)
        )

    # =========================================================
    # GROUP MEMBERS
    # =========================================================

    def show_group_members(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        try:
            text = self.group_os.render_members(
                chat_id
            )
        except Exception:
            text = (
                "👥 <b>УЧАСТНИКИ ГРУППЫ</b>\n\n"
                "Не удалось получить список участников."
            )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"},
                    {"text": "⬅️ Назад в Group OS"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    # =========================================================
    # MODERATION
    # =========================================================

    def show_group_moderation(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        is_admin = self.is_group_admin(
            chat_id,
            user_id
        )

        bot_member = self.get_bot_member(
            chat_id
        )

        bot_status = (
            bot_member.get("status")
            if bot_member
            else "unknown"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"},
                    {"text": "⬅️ Назад в Group OS"}
                ]
            ],
            "resize_keyboard": True
        }

        text = (
            "🛡 <b>МОДЕРАЦИЯ</b>\n\n"
            f"👤 <b>Ваш статус:</b> "
            f"{'Администратор' if is_admin else 'Участник'}\n"
            f"🤖 <b>Статус T-OS:</b> "
            f"{self.translate_member_status(bot_status)}\n\n"
            "Доступные возможности модуля:\n"
            "├ 🔇 Управление участниками\n"
            "├ 🚫 Блокировка\n"
            "├ 🔓 Разблокировка\n"
            "└ ⚙️ Контроль прав\n\n"
        )

        if not is_admin:
            text += (
                "ℹ️ Управление модерацией доступно "
                "администраторам группы."
            )
        else:
            text += (
                "🟢 У вас есть права администратора.\n"
                "Дополнительные действия можно выполнять "
                "после выбора конкретного участника."
            )

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def translate_member_status(self, status):
        values = {
            "creator": "Создатель",
            "administrator": "Администратор",
            "member": "Участник",
            "restricted": "Ограничен",
            "left": "Вышел",
            "kicked": "Заблокирован"
        }

        return values.get(
            status,
            "Неизвестно"
        )

    # =========================================================
    # GROUP AUDIT LOG
    # =========================================================

    def show_group_audit_log(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        try:
            logs = self.group_os.get_audit_log(
                chat_id,
                50
            )
        except Exception:
            logs = []

        text = "📜 <b>GROUP AUDIT LOG</b>\n\n"

        if not logs:
            text += "Журнал пока пуст."

        else:
            for log in logs:
                if isinstance(log, dict):
                    actor = log.get(
                        "actor_id",
                        "?"
                    )

                    action = log.get(
                        "action",
                        "unknown"
                    )

                    details = log.get(
                        "details",
                        ""
                    )

                    created = log.get(
                        "created_at",
                        ""
                    )

                    text += (
                        f"👤 <code>{actor}</code>\n"
                        f"⚙️ <b>{self.html_escape(action)}</b>\n"
                    )

                    if details:
                        text += (
                            f"📝 {self.html_escape(details)}\n"
                        )

                    if created:
                        text += (
                            f"🕒 {created}\n"
                        )

                    text += "\n"

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"},
                    {"text": "⬅️ Назад в Group OS"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    # =========================================================
    # PERMISSIONS
    # =========================================================

    def show_group_permissions(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        member = self.get_group_member(
            chat_id,
            user_id
        )

        status = (
            member.get("status")
            if member
            else "unknown"
        )

        is_admin = status in (
            "creator",
            "administrator"
        )

        bot_member = self.get_bot_member(
            chat_id
        )

        bot_admin = (
            bot_member
            and bot_member.get("status")
            in ("creator", "administrator")
        )

        text = (
            "⚙️ <b>ПРАВА ДОСТУПА</b>\n\n"
            f"👤 <b>Ваш статус:</b> "
            f"{self.translate_member_status(status)}\n\n"
            "👤 <b>Ваши права:</b>\n"
            f"{'🟢' if is_admin else '🔴'} "
            f"Администратор\n\n"
            "🤖 <b>Права T-OS:</b>\n"
            f"{'🟢' if bot_admin else '🔴'} "
            f"Администратор\n"
        )

        if bot_member:
            if bot_member.get("can_delete_messages"):
                text += "🟢 Удаление сообщений\n"

            if bot_member.get("can_restrict_members"):
                text += "🟢 Ограничение участников\n"

            if bot_member.get("can_invite_users"):
                text += "🟢 Приглашение пользователей\n"

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"},
                    {"text": "⬅️ Назад в Group OS"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    # =========================================================
    # GROUP AI SETTINGS
    # =========================================================

    def show_group_ai_settings(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        try:
            settings = self.group_os.get_settings(
                chat_id
            )
        except Exception:
            settings = {}

        ai_enabled = settings.get(
            "ai_enabled",
            True
        )

        if isinstance(ai_enabled, str):
            ai_enabled = ai_enabled.lower() in (
                "1",
                "true",
                "yes",
                "on"
            )

        status_text = (
            "🟢 ИИ включён"
            if ai_enabled
            else "🔴 ИИ выключен"
        )

        keyboard = {
            "keyboard": [
                [
                    {
                        "text": status_text
                    }
                ],
                [
                    {"text": "🔄 Обновить"},
                    {"text": "⬅️ Назад в Group OS"}
                ]
            ],
            "resize_keyboard": True
        }

        text = (
            "🤖 <b>НАСТРОЙКИ ИИ</b>\n\n"
            f"Статус: <b>{'ВКЛЮЧЕН' if ai_enabled else 'ВЫКЛЮЧЕН'}</b>\n\n"
            "Этот параметр хранится отдельно для каждой группы.\n\n"
            "Нажми кнопку статуса, чтобы изменить настройку."
        )

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def toggle_group_ai(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        if not self.is_group_admin(
            chat_id,
            user_id
        ):
            self.send_message(
                chat_id,
                "⛔ <b>Недостаточно прав</b>\n\n"
                "Изменять настройки ИИ может только "
                "администратор группы."
            )
            return

        try:
            new_value = self.group_os.toggle_ai(
                chat_id
            )

            self.group_os.audit(
                chat_id,
                user_id,
                "ai_toggle",
                f"AI enabled: {new_value}"
            )

            self.show_group_ai_settings(
                chat_id,
                user_id
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось изменить настройку ИИ."
            )

    # =========================================================
    # GROUP STATISTICS
    # =========================================================

    def show_group_statistics(self, chat_id, user_id):
        chat = self.get_group_chat(chat_id)

        if not self.is_group(chat):
            self.send_message(
                chat_id,
                "⚠️ Раздел доступен только в группе."
            )
            return

        try:
            statistics = self.group_os.get_statistics(
                chat_id
            )
        except Exception:
            statistics = {}

        try:
            settings = self.group_os.get_settings(
                chat_id
            )
        except Exception:
            settings = {}

        messages = statistics.get(
            "messages",
            0
        )

        commands = statistics.get(
            "commands",
            0
        )

        users = statistics.get(
            "users",
            0
        )

        moderation = statistics.get(
            "moderation_actions",
            0
        )

        ai_enabled = settings.get(
            "ai_enabled",
            True
        )

        if isinstance(ai_enabled, str):
            ai_enabled = ai_enabled.lower() in (
                "1",
                "true",
                "yes",
                "on"
            )

        text = (
            "📊 <b>СТАТИСТИКА ГРУППЫ</b>\n\n"
            f"💬 <b>Сообщений:</b> {messages}\n"
            f"⌨️ <b>Команд:</b> {commands}\n"
            f"👥 <b>Активных пользователей:</b> {users}\n"
            f"🛡 <b>Модераций:</b> {moderation}\n\n"
            f"🤖 <b>ИИ:</b> "
            f"{'🟢 включён' if ai_enabled else '🔴 выключен'}"
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "🔄 Обновить"},
                    {"text": "⬅️ Назад в Group OS"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    # =========================================================
    # DEVELOPER PANEL
    # =========================================================

    def show_developer(self, chat_id, user_id):
        keyboard = {
            "keyboard": [
                [
                    {"text": "📊 Статистика"},
                    {"text": "👥 Пользователи"}
                ],
                [
                    {"text": "📜 Audit Log"},
                    {"text": "🗄 База данных"}
                ],
                [
                    {"text": "🖥 Система"},
                    {"text": "🧪 Experimental Lab"}
                ],
                [
                    {"text": "🖥️ Главное меню"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            "🛠 <b>DEVELOPER PANEL</b>\n\n"
            "Инструменты разработчика T-OS.",
            keyboard
        )

    def show_developer_stats(self, chat_id, user_id):
        try:
            info = self.developer.get_statistics()

            self.send_message(
                chat_id,
                "📊 <b>СТАТИСТИКА T-OS</b>\n\n"
                f"<pre>{self.html_escape(str(info))}</pre>"
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось получить статистику."
            )

    def show_developer_users(self, chat_id, user_id):
        try:
            users = self.developer.get_users()

            text = "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"

            if not users:
                text += "Пользователей нет."

            else:
                for user in users[:50]:
                    if isinstance(user, dict):
                        uid = user.get("user_id", "?")
                        username = user.get(
                            "username",
                            "нет"
                        )

                        text += (
                            f"👤 <code>{uid}</code> "
                            f"@{username}\n"
                        )
                    else:
                        text += f"👤 {user}\n"

            self.send_message(
                chat_id,
                text
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось загрузить пользователей."
            )

    def show_audit_log(self, chat_id, user_id):
        try:
            logs = self.database.get_audit_logs(
                limit=100
            )

            text = "📜 <b>AUDIT LOG</b>\n\n"

            if not logs:
                text += "Журнал пуст."

            else:
                for log in logs:
                    if isinstance(log, dict):
                        actor = log.get(
                            "actor_id",
                            "?"
                        )
                        action = log.get(
                            "action",
                            "unknown"
                        )
                        target = log.get(
                            "target_id",
                            ""
                        )
                        details = log.get(
                            "details",
                            ""
                        )

                        text += (
                            f"👤 <code>{actor}</code>\n"
                            f"⚙️ {self.html_escape(action)}\n"
                        )

                        if target:
                            text += (
                                f"🎯 <code>{target}</code>\n"
                            )

                        if details:
                            text += (
                                f"📝 {self.html_escape(details)}\n"
                            )

                        text += "\n"

            self.send_message(
                chat_id,
                text
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось загрузить Audit Log."
            )

    def show_database_info(self, chat_id, user_id):
        try:
            info = self.developer.get_database_info()

            self.send_message(
                chat_id,
                "🗄 <b>DATABASE</b>\n\n"
                f"<pre>{self.html_escape(str(info))}</pre>"
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось получить информацию о БД."
            )

    def show_system_info(self, chat_id, user_id):
        try:
            info = self.developer.get_system_info()

            self.send_message(
                chat_id,
                "🖥 <b>SYSTEM</b>\n\n"
                f"<pre>{self.html_escape(str(info))}</pre>"
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚠️ Не удалось получить информацию о системе."
            )

    def show_experimental_lab(self, chat_id, user_id):
        self.send_message(
            chat_id,
            "🧪 <b>EXPERIMENTAL LAB</b>\n\n"
            "Экспериментальные функции T-OS."
        )

    # =========================================================
    # GAMES
    # =========================================================

    def show_games(self, chat_id, user_id):
        keyboard = {
            "keyboard": [
                [
                    {"text": "🎲 Кубик"},
                    {"text": "🔢 Угадай число"}
                ],
                [
                    {"text": "🧠 Викторина"},
                    {"text": "🧩 Загадка"}
                ],
                [
                    {"text": "⚡ Реакция"}
                ],
                [
                    {"text": "🖥️ Главное меню"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            "🎮 <b>T-OS GAMES</b>\n\n"
            "Выбери игру:",
            keyboard
        )

    def start_dice(self, chat_id, user_id):
        try:
            result = self.games.start_dice(
                chat_id,
                user_id
            )

            self.send_message(
                chat_id,
                str(result)
            )

        except Exception:
            self.send_message(
                chat_id,
                "🎲 Не удалось запустить игру."
            )

    def start_guess(self, chat_id, user_id):
        try:
            result = self.games.start_guess(
                chat_id,
                user_id
            )

            self.send_message(
                chat_id,
                str(result)
            )

        except Exception:
            self.send_message(
                chat_id,
                "🔢 Не удалось запустить игру."
            )

    def start_quiz(self, chat_id, user_id):
        try:
            result = self.games.start_quiz(
                chat_id,
                user_id
            )

            self.send_message(
                chat_id,
                str(result)
            )

        except Exception:
            self.send_message(
                chat_id,
                "🧠 Не удалось запустить викторину."
            )

    def start_riddle(self, chat_id, user_id):
        try:
            result = self.games.start_riddle(
                chat_id,
                user_id
            )

            self.send_message(
                chat_id,
                str(result)
            )

        except Exception:
            self.send_message(
                chat_id,
                "🧩 Не удалось запустить загадку."
            )

    def start_reaction(self, chat_id, user_id):
        try:
            result = self.games.start_reaction(
                chat_id,
                user_id
            )

            self.send_message(
                chat_id,
                str(result)
            )

        except Exception:
            self.send_message(
                chat_id,
                "⚡ Не удалось запустить игру."
            )