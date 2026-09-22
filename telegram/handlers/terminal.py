from html import escape


class TerminalHandler:

    def __init__(self, bot, database, filesystem):
        self.bot = bot
        self.database = database
        self.filesystem = filesystem

    def send_message(self, chat_id, text, reply_markup=None):
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

    def show_terminal(self, chat_id, user_id):
        keyboard = {
            "keyboard": [
                [
                    {"text": "📂 ls"},
                    {"text": "📍 pwd"}
                ],
                [
                    {"text": "📁 mkdir"},
                    {"text": "📄 touch"}
                ],
                [
                    {"text": "🧹 clear"}
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
                "💻 <b>T-OS TERMINAL</b>\n\n"
                "Виртуальный терминал T-OS.\n\n"
                "Доступные команды:\n"
                "<code>/help</code> — помощь\n"
                "<code>/ls</code> — список файлов\n"
                "<code>/cd</code> — перейти в папку\n"
                "<code>/pwd</code> — текущая папка\n"
                "<code>/touch</code> — создать файл\n"
                "<code>/mkdir</code> — создать папку\n"
                "<code>/cat</code> — прочитать файл\n"
                "<code>/write</code> — изменить файл\n"
                "<code>/rm</code> — удалить файл\n"
                "<code>/clear</code> — очистить экран"
            ),
            keyboard
        )

    def get_directory(self, user_id):
        return self.filesystem.get_current_directory(user_id)

    def normalize_path(self, user_id, path):
        current = self.get_directory(user_id)

        if not path:
            return current

        path = path.strip()

        if path == "/":
            return "/"

        if path.startswith("/"):
            return path.strip("/")

        if current == "/":
            return path.strip("/")

        return current.lstrip("/") + path.strip("/")

    def command_help(self, chat_id):
        self.send_message(
            chat_id,
            (
                "💻 <b>TERMINAL HELP</b>\n\n"
                "<code>/ls</code>\n"
                "Показать содержимое текущей папки.\n\n"

                "<code>/pwd</code>\n"
                "Показать текущий путь.\n\n"

                "<code>/cd папка</code>\n"
                "Перейти в папку.\n\n"

                "<code>/cd ..</code>\n"
                "Перейти на уровень выше.\n\n"

                "<code>/touch файл.txt</code>\n"
                "Создать файл.\n\n"

                "<code>/mkdir папка</code>\n"
                "Создать папку.\n\n"

                "<code>/cat файл.txt</code>\n"
                "Показать содержимое файла.\n\n"

                "<code>/write файл.txt текст</code>\n"
                "Записать текст в файл.\n\n"

                "<code>/rm файл.txt</code>\n"
                "Удалить файл.\n\n"

                "<code>/clear</code>\n"
                "Очистить состояние терминала."
            )
        )

    def command_pwd(self, chat_id, user_id):
        directory = self.get_directory(user_id)

        self.send_message(
            chat_id,
            (
                "📍 <b>Текущая директория:</b>\n\n"
                f"<code>{escape(directory)}</code>"
            )
        )

    def command_ls(self, chat_id, user_id):
        directory = self.get_directory(user_id)

        try:
            files = self.database.get_files(
                user_id,
                directory
            )
        except Exception:
            files = []

        result = []

        for file in files:
            try:
                path = file["path"]
                file_type = file["file_type"]
            except Exception:
                continue

            if directory == "/":
                relative = path
            else:
                prefix = directory.lstrip("/")

                if not path.startswith(prefix):
                    continue

                relative = path[len(prefix):]

            relative = relative.lstrip("/")

            if not relative:
                continue

            if "/" in relative.rstrip("/"):
                continue

            if file_type == "folder":
                result.append(
                    f"📁 {escape(relative.rstrip('/'))}"
                )
            else:
                result.append(
                    f"📄 {escape(relative)}"
                )

        if not result:
            result_text = "📭 Папка пуста."
        else:
            result_text = "\n".join(result)

        self.send_message(
            chat_id,
            (
                "💻 <b>ls</b>\n\n"
                f"📍 <code>{escape(directory)}</code>\n\n"
                f"{result_text}"
            )
        )

    def command_cd(self, chat_id, user_id, argument):
        if not argument:
            self.filesystem.set_current_directory(
                user_id,
                "/"
            )

            self.command_pwd(
                chat_id,
                user_id
            )
            return

        argument = argument.strip()

        if argument == ".":
            self.command_pwd(
                chat_id,
                user_id
            )
            return

        if argument == "..":
            self.filesystem.go_back(
                chat_id,
                user_id
            )
            return

        target = self.normalize_path(
            user_id,
            argument
        )

        if not target:
            target = "/"

        if target == "/":
            self.filesystem.set_current_directory(
                user_id,
                "/"
            )

            self.command_pwd(
                chat_id,
                user_id
            )
            return

        if not target.endswith("/"):
            target += "/"

        try:
            folder = self.database.get_file(
                user_id,
                target
            )
        except Exception:
            folder = None

        if not folder:
            self.send_message(
                chat_id,
                (
                    "❌ Папка не найдена:\n"
                    f"<code>{escape(target)}</code>"
                )
            )
            return

        try:
            file_type = folder["file_type"]
        except Exception:
            file_type = None

        if file_type != "folder":
            self.send_message(
                chat_id,
                "❌ Это не папка."
            )
            return

        self.filesystem.set_current_directory(
            user_id,
            target
        )

        self.send_message(
            chat_id,
            (
                "✅ Переход выполнен.\n\n"
                f"📍 <code>{escape(target)}</code>"
            )
        )

    def command_touch(self, chat_id, user_id, filename):
        if not filename:
            self.send_message(
                chat_id,
                (
                    "❌ Укажите имя файла.\n\n"
                    "<code>/touch example.txt</code>"
                )
            )
            return

        filename = filename.strip()

        if "/" in filename:
            self.send_message(
                chat_id,
                "❌ Имя файла не должно содержать <code>/</code>."
            )
            return

        if filename in (".", ".."):
            self.send_message(
                chat_id,
                "❌ Такое имя использовать нельзя."
            )
            return

        directory = self.get_directory(user_id)

        path = (
            filename
            if directory == "/"
            else directory.lstrip("/") + filename
        )

        try:
            if self.database.path_exists(
                user_id,
                path
            ):
                self.send_message(
                    chat_id,
                    "⚠️ Такой файл или папка уже существует."
                )
                return

            self.database.create_file(
                user_id,
                path,
                "file",
                ""
            )

            self.send_message(
                chat_id,
                (
                    "✅ Файл создан.\n\n"
                    f"📄 <code>{escape(path)}</code>"
                )
            )

        except Exception:
            self.send_message(
                chat_id,
                "❌ Не удалось создать файл."
            )

    def command_mkdir(self, chat_id, user_id, dirname):
        if not dirname:
            self.send_message(
                chat_id,
                (
                    "❌ Укажите имя папки.\n\n"
                    "<code>/mkdir documents</code>"
                )
            )
            return

        dirname = dirname.strip().strip("/")

        if not dirname:
            self.send_message(
                chat_id,
                "❌ Некорректное имя папки."
            )
            return

        if "/" in dirname:
            self.send_message(
                chat_id,
                "❌ Имя папки не должно содержать <code>/</code>."
            )
            return

        if dirname in (".", ".."):
            self.send_message(
                chat_id,
                "❌ Такое имя использовать нельзя."
            )
            return

        directory = self.get_directory(user_id)

        path = (
            dirname + "/"
            if directory == "/"
            else directory.lstrip("/")
            + dirname
            + "/"
        )

        try:
            if self.database.path_exists(
                user_id,
                path
            ):
                self.send_message(
                    chat_id,
                    "⚠️ Такая папка уже существует."
                )
                return

            self.database.create_file(
                user_id,
                path,
                "folder",
                ""
            )

            self.send_message(
                chat_id,
                (
                    "✅ Папка создана.\n\n"
                    f"📁 <code>{escape(path)}</code>"
                )
            )

        except Exception:
            self.send_message(
                chat_id,
                "❌ Не удалось создать папку."
            )

    def command_cat(self, chat_id, user_id, filename):
        if not filename:
            self.send_message(
                chat_id,
                (
                    "❌ Укажите файл.\n\n"
                    "<code>/cat hello.txt</code>"
                )
            )
            return

        path = self.normalize_path(
            user_id,
            filename
        )

        try:
            file = self.database.get_file(
                user_id,
                path
            )
        except Exception:
            file = None

        if not file:
            self.send_message(
                chat_id,
                (
                    "❌ Файл не найден:\n"
                    f"<code>{escape(path)}</code>"
                )
            )
            return

        try:
            file_type = file["file_type"]
            content = file["content"] or ""
        except Exception:
            self.send_message(
                chat_id,
                "❌ Не удалось прочитать файл."
            )
            return

        if file_type == "folder":
            self.send_message(
                chat_id,
                "❌ Нельзя прочитать папку как файл."
            )
            return

        if not content:
            content = "📭 Файл пуст."

        if len(content) > 3500:
            content = content[:3500] + "\n..."

        self.send_message(
            chat_id,
            (
                "📄 <b>cat</b>\n\n"
                f"📌 <code>{escape(path)}</code>\n\n"
                f"<pre>{escape(content)}</pre>"
            )
        )

    def command_write(self, chat_id, user_id, argument):
        if not argument:
            self.send_message(
                chat_id,
                (
                    "❌ Использование:\n\n"
                    "<code>/write файл.txt текст</code>"
                )
            )
            return

        parts = argument.split(
            " ",
            1
        )

        if len(parts) < 2:
            self.send_message(
                chat_id,
                (
                    "❌ Нужно указать файл и текст.\n\n"
                    "<code>/write hello.txt Привет</code>"
                )
            )
            return

        filename = parts[0]
        content = parts[1]

        path = self.normalize_path(
            user_id,
            filename
        )

        try:
            file = self.database.get_file(
                user_id,
                path
            )
        except Exception:
            file = None

        if not file:
            self.send_message(
                chat_id,
                "❌ Файл не найден."
            )
            return

        try:
            file_type = file["file_type"]
        except Exception:
            file_type = "file"

        if file_type == "folder":
            self.send_message(
                chat_id,
                "❌ Нельзя записывать текст в папку."
            )
            return

        try:
            self.database.update_file(
                user_id,
                path,
                content
            )

            self.send_message(
                chat_id,
                (
                    "✅ Файл обновлён.\n\n"
                    f"📄 <code>{escape(path)}</code>"
                )
            )

        except Exception:
            self.send_message(
                chat_id,
                "❌ Не удалось записать файл."
            )

    def command_rm(self, chat_id, user_id, filename):
        if not filename:
            self.send_message(
                chat_id,
                (
                    "❌ Укажите файл.\n\n"
                    "<code>/rm hello.txt</code>"
                )
            )
            return

        path = self.normalize_path(
            user_id,
            filename
        )

        try:
            file = self.database.get_file(
                user_id,
                path
            )
        except Exception:
            file = None

        if not file:
            self.send_message(
                chat_id,
                "❌ Файл не найден."
            )
            return

        try:
            file_type = file["file_type"]
        except Exception:
            file_type = "file"

        if file_type == "folder":
            self.send_message(
                chat_id,
                (
                    "❌ Удаление папок через <code>/rm</code> "
                    "пока не поддерживается."
                )
            )
            return

        try:
            self.database.delete_file(
                user_id,
                path
            )

            self.send_message(
                chat_id,
                (
                    "🗑 Файл удалён.\n\n"
                    f"<code>{escape(path)}</code>"
                )
            )

        except Exception:
            self.send_message(
                chat_id,
                "❌ Не удалось удалить файл."
            )

    def command_clear(self, chat_id, user_id):
        self.filesystem.cancel(
            user_id
        )

        self.send_message(
            chat_id,
            (
                "🧹 <b>TERMINAL CLEARED</b>\n\n"
                "Состояние терминала очищено."
            )
        )

    def handle_command(self, chat_id, user_id, text):
        if not text.startswith("/"):
            return False

        parts = text.split(
            " ",
            1
        )

        command = parts[0].lower()
        argument = (
            parts[1].strip()
            if len(parts) > 1
            else ""
        )

        if command == "/help":
            self.command_help(chat_id)
            return True

        if command == "/ls":
            self.command_ls(
                chat_id,
                user_id
            )
            return True

        if command == "/pwd":
            self.command_pwd(
                chat_id,
                user_id
            )
            return True

        if command == "/cd":
            self.command_cd(
                chat_id,
                user_id,
                argument
            )
            return True

        if command == "/touch":
            self.command_touch(
                chat_id,
                user_id,
                argument
            )
            return True

        if command == "/mkdir":
            self.command_mkdir(
                chat_id,
                user_id,
                argument
            )
            return True

        if command == "/cat":
            self.command_cat(
                chat_id,
                user_id,
                argument
            )
            return True

        if command == "/write":
            self.command_write(
                chat_id,
                user_id,
                argument
            )
            return True

        if command == "/rm":
            self.command_rm(
                chat_id,
                user_id,
                argument
            )
            return True

        if command == "/clear":
            self.command_clear(
                chat_id,
                user_id
            )
            return True

        return False