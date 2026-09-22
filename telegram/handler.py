from telegram.bot import TelegramBot
from datetime import datetime


class TelegramHandler:
    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

        self.file_states = {}
        self.terminal_dirs = {}
        self.command_history = {}

    def handle_update(self, update):
        message = update.get("message")

        if not message:
            return

        text = message.get("text", "")
        chat_id = message["chat"]["id"]

        user = message.get("from", {})
        user_id = user.get("id")

        if user_id:
            self.database.create_user(
                user_id,
                user.get("username")
            )

        # -------------------------
        # FILE STATES
        # -------------------------

        state = self.file_states.get(user_id)

        if state == "waiting_filename":
            self.create_new_file(
                chat_id,
                user_id,
                text
            )
            return

        if state and state.startswith("editing:"):
            path = state.replace("editing:", "", 1)

            self.save_file_content(
                chat_id,
                user_id,
                path,
                text
            )
            return

        if state and state.startswith("opened:"):

            if text == "✏️ Редактировать":
                path = state.replace("opened:", "", 1)

                self.start_editing(
                    chat_id,
                    user_id,
                    path
                )
                return

            if text == "📁 Файлы":
                self.file_states.pop(user_id, None)
                self.show_files(chat_id, user_id)
                return

        # -------------------------
        # TERMINAL
        # -------------------------

        if text.startswith("$"):
            self.handle_terminal(
                chat_id,
                user_id,
                text
            )
            return

        # -------------------------
        # MENU
        # -------------------------

        if text == "/start":
            self.file_states.pop(user_id, None)
            self.show_home(chat_id)

        elif text == "📁 Файлы":
            self.file_states.pop(user_id, None)
            self.show_files(chat_id, user_id)

        elif text == "📄 Создать файл":
            self.ask_filename(chat_id, user_id)

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
            self.show_notes(chat_id)

        elif text == "💻 Терминал":
            self.show_terminal(
                chat_id,
                user_id
            )

        elif text == "🧮 Калькулятор":
            self.show_calculator(chat_id)

        elif text == "🎮 Игры":
            self.show_games(chat_id)

        elif text == "⚙️ Настройки":
            self.show_settings(chat_id)

        elif text == "👤 Профиль":
            self.show_profile(
                chat_id,
                message
            )

        elif text == "📦 App Store":
            self.show_app_store(chat_id)

        elif text == "🖥️ Главное меню":
            self.file_states.pop(user_id, None)
            self.show_home(chat_id)

        elif text.startswith("📄 "):
            filename = text[2:].strip()

            self.open_file(
                chat_id,
                user_id,
                f"/home/user/Documents/{filename}"
            )

    # =========================================================
    # TELEGRAM
    # =========================================================

    def send_message(self, chat_id, text, keyboard=None):
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
                {"text": "📦 App Store"}
            ]
        ]

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

    def show_files(self, chat_id, user_id):
        self.initialize_filesystem(user_id)

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

    def ask_filename(self, chat_id, user_id):
        self.file_states[user_id] = "waiting_filename"

        self.send_message(
            chat_id,
            "📄 Введите имя файла:\n\n"
            "Например:\n"
            "hello.txt\n"
            "notes.md\n"
            "test.py"
        )

    def create_new_file(self, chat_id, user_id, filename):
        filename = filename.strip()

        if not filename:
            self.send_message(
                chat_id,
                "❌ Имя файла не может быть пустым."
            )
            return

        if "/" in filename or "\\" in filename:
            self.file_states.pop(user_id, None)

            self.send_message(
                chat_id,
                "❌ В имени файла нельзя использовать / или \\."
            )
            return

        if len(filename) > 100:
            self.file_states.pop(user_id, None)

            self.send_message(
                chat_id,
                "❌ Имя файла слишком длинное."
            )
            return

        self.initialize_filesystem(user_id)

        path = f"/home/user/Documents/{filename}"

        if self.database.path_exists(
            user_id,
            path
        ):
            self.file_states.pop(user_id, None)

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

        self.file_states.pop(user_id, None)

        self.send_message(
            chat_id,
            f"✅ Файл создан!\n\n"
            f"📄 {filename}\n"
            f"📍 {path}"
        )

    def show_directory(self, chat_id, user_id, directory):
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

            if path.count("/") != directory.count("/") + 1:
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

    def open_file(self, chat_id, user_id, path):
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

        self.file_states[user_id] = f"opened:{path}"

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

    def start_editing(self, chat_id, user_id, path):
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

        self.file_states[user_id] = f"editing:{path}"

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

        self.file_states.pop(
            user_id,
            None
        )

        filename = path.split("/")[-1]

        self.send_message(
            chat_id,
            f"✅ Файл сохранён!\n\n"
            f"📄 {filename}\n"
            f"📍 {path}"
        )

    # =========================================================
    # TERMINAL CORE
    # =========================================================

    def get_terminal_dir(self, user_id):
        return self.terminal_dirs.get(
            user_id,
            "/home/user"
        )

    def set_terminal_dir(self, user_id, path):
        self.terminal_dirs[user_id] = path

    def normalize_path(self, current_dir, target):
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

    def terminal_output(self, chat_id, text):
        self.send_message(
            chat_id,
            text
        )

    def add_history(self, user_id, command):
        if user_id not in self.command_history:
            self.command_history[user_id] = []

        self.command_history[user_id].append(
            command
        )

        # Максимум 50 последних команд
        self.command_history[user_id] = (
            self.command_history[user_id][-50:]
        )

    def handle_terminal(self, chat_id, user_id, text):
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

        parts = command_line.split()

        command = parts[0].lower()
        args = parts[1:]

        current_dir = self.get_terminal_dir(
            user_id
        )

        self.initialize_filesystem(
            user_id
        )

        # =====================================================
        # HELP
        # =====================================================

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

        # =====================================================
        # PWD
        # =====================================================

        if command == "pwd":
            self.terminal_output(
                chat_id,
                current_dir
            )
            return

        # =====================================================
        # WHOAMI
        # =====================================================

        if command == "whoami":
            self.terminal_output(
                chat_id,
                f"tos-user-{user_id}"
            )
            return

        # =====================================================
        # DATE
        # =====================================================

        if command == "date":
            now = datetime.now()

            self.terminal_output(
                chat_id,
                now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            return

        # =====================================================
        # CLEAR
        # =====================================================

        if command == "clear":
            self.terminal_output(
                chat_id,
                "🧹 Terminal cleared."
            )
            return

        # =====================================================
        # LS
        # =====================================================

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

        # =====================================================
        # CD
        # =====================================================

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

        # =====================================================
        # TOUCH
        # =====================================================

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

            self.terminal_output(
                chat_id,
                f"✅ Создан файл: {filename}"
            )
            return

        # =====================================================
        # MKDIR
        # =====================================================

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

            self.terminal_output(
                chat_id,
                f"✅ Создана папка: {dirname}"
            )
            return

        # =====================================================
        # CAT
        # =====================================================

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

        # =====================================================
        # WRITE
        # =====================================================

        if command == "write":

            if len(args) < 2:
                self.terminal_output(
                    chat_id,
                    "Использование:\n"
                    "$ write filename text"
                )
                return

            filename = args[0]

            content = " ".join(
                args[1:]
            )

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

            self.terminal_output(
                chat_id,
                "✅ Файл записан."
            )
            return

        # =====================================================
        # ECHO
        # =====================================================

        if command == "echo":

            self.terminal_output(
                chat_id,
                " ".join(args)
            )
            return

        # =====================================================
        # RM
        # =====================================================

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

        # =====================================================
        # CP
        # =====================================================

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

            self.terminal_output(
                chat_id,
                f"📋 Скопировано: {args[0]} → {args[1]}"
            )
            return

        # =====================================================
        # MV
        # =====================================================

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

            self.terminal_output(
                chat_id,
                f"📦 Перемещено: {args[0]} → {args[1]}"
            )
            return

        # =====================================================
        # TREE
        # =====================================================

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

        # =====================================================
        # HISTORY
        # =====================================================

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

        # =====================================================
        # NEOFETCH
        # =====================================================

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

        # =====================================================
        # UNKNOWN
        # =====================================================

        self.terminal_output(
            chat_id,
            f"❌ Команда не найдена: {command}\n\n"
            "Введите $ help"
        )

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

            if path.count("/") != directory.count("/") + 1:
                continue

            children.append(file)

        for index, file in enumerate(children):
            path = file[1]
            file_type = file[2]

            is_last = index == len(children) - 1

            branch = "└── " if is_last else "├── "

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
    # OTHER APPS
    # =========================================================

    def show_terminal(self, chat_id, user_id):
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

    def show_profile(self, chat_id, message):
        user = message.get("from", {})

        user_id = user.get(
            "id",
            "неизвестно"
        )

        username = user.get(
            "username"
        )

        if username:
            username = f"@{username}"
        else:
            username = "не установлен"

        self.send_message(
            chat_id,
            "👤 ПРОФИЛЬ T-OS\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Username: {username}\n\n"
            "⭐ Уровень: 1\n"
            "✨ XP: 0\n"
            "🪙 T-Coins: 0"
        )

    def show_notes(self, chat_id):
        self.send_message(
            chat_id,
            "📝 ЗАМЕТКИ\n\n"
            "Система заметок T-OS находится в разработке."
        )

    def show_calculator(self, chat_id):
        self.send_message(
            chat_id,
            "🧮 КАЛЬКУЛЯТОР\n\n"
            "Калькулятор T-OS находится в разработке."
        )

    def show_games(self, chat_id):
        self.send_message(
            chat_id,
            "🎮 ИГРЫ T-OS\n\n"
            "🎲 Dice\n"
            "🧠 Quiz\n"
            "🔢 Guess Number\n"
            "🧩 Riddles\n"
            "⚡ Reaction"
        )

    def show_settings(self, chat_id):
        self.send_message(
            chat_id,
            "⚙️ НАСТРОЙКИ T-OS\n\n"
            "🌐 Язык: 🇷🇺 Русский\n"
            "🔔 Уведомления: включены\n"
            "🖥️ Режим: Personal OS"
        )

    def show_app_store(self, chat_id):
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