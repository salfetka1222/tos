from html import escape


class FilesystemHandler:

    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

        # Состояния пользователей:
        # {
        #     user_id: {
        #         "action": "...",
        #         "path": "..."
        #     }
        # }
        self.states = {}

        # Текущая директория пользователя
        self.current_dirs = {}

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

    # =====================================================
    # PATH
    # =====================================================

    def normalize_directory(self, directory):
        if not directory:
            return "/"

        directory = str(directory).strip()

        if directory == "/":
            return "/"

        directory = "/" + directory.strip("/")
        return directory + "/"

    def normalize_file_path(self, path):
        if not path:
            return ""

        path = str(path).strip()

        if path == "/":
            return "/"

        return path.strip("/")

    def get_current_directory(
        self,
        user_id
    ):
        return self.current_dirs.get(
            user_id,
            "/"
        )

    def set_current_directory(
        self,
        user_id,
        directory
    ):
        self.current_dirs[user_id] = (
            self.normalize_directory(directory)
        )

    # =====================================================
    # MAIN FILESYSTEM
    # =====================================================

    def show_filesystem(
        self,
        chat_id,
        user_id
    ):
        self.set_current_directory(
            user_id,
            "/"
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
            (
                "📁 <b>ФАЙЛОВАЯ СИСТЕМА</b>\n\n"
                "Добро пожаловать в файловую систему T-OS.\n\n"
                "Выберите действие:"
            ),
            keyboard
        )

    # =====================================================
    # FILE LIST
    # =====================================================

    def show_files(
        self,
        chat_id,
        user_id,
        directory=None
    ):
        if directory is None:
            directory = self.get_current_directory(
                user_id
            )

        directory = self.normalize_directory(
            directory
        )

        self.set_current_directory(
            user_id,
            directory
        )

        try:
            files = self.database.get_files(
                user_id,
                directory
            )
        except Exception:
            files = []

        lines = [
            "📂 <b>МОИ ФАЙЛЫ</b>",
            "",
            f"📍 Путь: <code>{escape(directory)}</code>",
            ""
        ]

        keyboard_rows = []

        # -------------------------------------------------
        # DIRECT CHILDREN ONLY
        # -------------------------------------------------

        direct_files = []

        for file in files:
            try:
                path = file["path"]
                file_type = file["file_type"]
            except Exception:
                continue

            path = str(path)

            # Убираем путь текущей директории
            if directory == "/":
                relative = path
            else:
                prefix = directory.lstrip("/")

                if path.startswith(prefix):
                    relative = path[len(prefix):]
                else:
                    continue

            relative = relative.lstrip("/")

            if not relative:
                continue

            # Для папок путь заканчивается /
            if file_type == "folder":
                folder_name = relative.rstrip("/")

                # Не показываем вложенные папки
                if "/" in folder_name:
                    continue

                direct_files.append(
                    (
                        path,
                        file_type,
                        folder_name
                    )
                )

            else:
                # Не показываем файлы из вложенных директорий
                if "/" in relative:
                    continue

                direct_files.append(
                    (
                        path,
                        file_type,
                        relative
                    )
                )

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        direct_files.sort(
            key=lambda item: (
                0 if item[1] == "folder" else 1,
                item[2].lower()
            )
        )

        # -------------------------------------------------
        # EMPTY
        # -------------------------------------------------

        if not direct_files:
            lines.append(
                "📭 В этой папке пока ничего нет."
            )

        # -------------------------------------------------
        # BUTTONS
        # -------------------------------------------------

        for path, file_type, name in direct_files:

            safe_name = escape(
                name
            )

            if file_type == "folder":
                icon = "📁"

                keyboard_rows.append(
                    [
                        {
                            "text": f"{icon} {name}"
                        }
                    ]
                )

                lines.append(
                    f"📁 <code>{safe_name}</code>"
                )

            else:
                icon = "📄"

                keyboard_rows.append(
                    [
                        {
                            "text": f"{icon} {name}"
                        }
                    ]
                )

                lines.append(
                    f"📄 <code>{safe_name}</code>"
                )

        # -------------------------------------------------
        # NAVIGATION
        # -------------------------------------------------

        keyboard_rows.append(
            [
                {"text": "📄 Создать файл"},
                {"text": "📁 Создать папку"}
            ]
        )

        keyboard_rows.append(
            [
                {"text": "🔄 Обновить"}
            ]
        )

        if directory != "/":
            keyboard_rows.append(
                [
                    {"text": "⬅️ Назад"}
                ]
            )

        keyboard_rows.append(
            [
                {"text": "🏠 Главная"}
            ]
        )

        keyboard = {
            "keyboard": keyboard_rows,
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            "\n".join(lines),
            keyboard
        )

    # =====================================================
    # CREATE FILE
    # =====================================================

    def create_file_start(
        self,
        chat_id,
        user_id
    ):
        current_directory = (
            self.get_current_directory(
                user_id
            )
        )

        self.states[user_id] = {
            "action": "create_file",
            "directory": current_directory
        }

        self.send_message(
            chat_id,
            (
                "📄 <b>СОЗДАНИЕ ФАЙЛА</b>\n\n"
                f"📍 Папка: <code>{escape(current_directory)}</code>\n\n"
                "Введите имя файла.\n\n"
                "Например:\n"
                "<code>hello.txt</code>"
            )
        )

    # =====================================================
    # CREATE FOLDER
    # =====================================================

    def create_folder_start(
        self,
        chat_id,
        user_id
    ):
        current_directory = (
            self.get_current_directory(
                user_id
            )
        )

        self.states[user_id] = {
            "action": "create_folder",
            "directory": current_directory
        }

        self.send_message(
            chat_id,
            (
                "📁 <b>СОЗДАНИЕ ПАПКИ</b>\n\n"
                f"📍 Папка: <code>{escape(current_directory)}</code>\n\n"
                "Введите имя папки.\n\n"
                "Например:\n"
                "<code>documents</code>"
            )
        )

    # =====================================================
    # INPUT HANDLER
    # =====================================================

    def handle_input(
        self,
        chat_id,
        user_id,
        text
    ):
        state = self.states.get(
            user_id
        )

        if not state:
            return False

        text = text.strip()

        if not text:
            self.send_message(
                chat_id,
                "❌ Имя не может быть пустым."
            )
            return True

        action = state.get(
            "action"
        )

        directory = self.normalize_directory(
            state.get(
                "directory",
                "/"
            )
        )

        # -------------------------------------------------
        # CREATE FILE
        # -------------------------------------------------

        if action == "create_file":

            if "/" in text:
                self.send_message(
                    chat_id,
                    "❌ Имя файла не должно содержать символ <code>/</code>."
                )
                return True

            if text in (".", ".."):
                self.send_message(
                    chat_id,
                    "❌ Такое имя использовать нельзя."
                )
                return True

            path = (
                text
                if directory == "/"
                else directory.lstrip("/") + text
            )

            try:
                if self.database.path_exists(
                    user_id,
                    path
                ):
                    self.send_message(
                        chat_id,
                        (
                            "⚠️ Файл или папка с таким именем "
                            "уже существует."
                        )
                    )
                    return True

                self.database.create_file(
                    user_id,
                    path,
                    "file",
                    ""
                )

                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    (
                        f"✅ Файл <b>{escape(text)}</b> создан.\n\n"
                        f"📍 Путь: <code>{escape(path)}</code>"
                    )
                )

                self.show_files(
                    chat_id,
                    user_id,
                    directory
                )

            except Exception:
                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    "❌ Не удалось создать файл."
                )

            return True

        # -------------------------------------------------
        # CREATE FOLDER
        # -------------------------------------------------

        if action == "create_folder":

            if "/" in text:
                self.send_message(
                    chat_id,
                    "❌ Имя папки не должно содержать символ <code>/</code>."
                )
                return True

            if text in (".", ".."):
                self.send_message(
                    chat_id,
                    "❌ Такое имя использовать нельзя."
                )
                return True

            path = (
                text.rstrip("/") + "/"
                if directory == "/"
                else directory.lstrip("/")
                + text.rstrip("/")
                + "/"
            )

            try:
                if self.database.path_exists(
                    user_id,
                    path
                ):
                    self.send_message(
                        chat_id,
                        (
                            "⚠️ Папка с таким именем "
                            "уже существует."
                        )
                    )
                    return True

                self.database.create_file(
                    user_id,
                    path,
                    "folder",
                    ""
                )

                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    (
                        f"✅ Папка <b>{escape(text)}</b> создана.\n\n"
                        f"📍 Путь: <code>{escape(path)}</code>"
                    )
                )

                self.show_files(
                    chat_id,
                    user_id,
                    directory
                )

            except Exception:
                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    "❌ Не удалось создать папку."
                )

            return True

        return False

    # =====================================================
    # OPEN PATH
    # =====================================================

    def open_path(
        self,
        chat_id,
        user_id,
        path
    ):
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
                "❌ Файл или папка не найдены."
            )
            return

        try:
            file_type = file["file_type"]
        except Exception:
            file_type = "file"

        if file_type == "folder":

            directory = self.normalize_directory(
                path
            )

            self.set_current_directory(
                user_id,
                directory
            )

            self.show_files(
                chat_id,
                user_id,
                directory
            )

            return

        self.open_file(
            chat_id,
            user_id,
            path
        )

    # =====================================================
    # OPEN FILE
    # =====================================================

    def open_file(
        self,
        chat_id,
        user_id,
        path
    ):
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
            self.show_files(
                chat_id,
                user_id,
                self.normalize_directory(path)
            )
            return

        try:
            content = file["content"] or ""
        except Exception:
            content = ""

        if not content:
            content = "📭 Файл пуст."

        if len(content) > 3500:
            content = content[:3500] + "\n\n..."

        safe_path = escape(
            path
        )

        safe_content = escape(
            content
        )

        keyboard = {
            "keyboard": [
                [
                    {"text": "✏️ Изменить файл"},
                    {"text": "🗑 Удалить файл"}
                ],
                [
                    {"text": "⬅️ Назад"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        self.states[user_id] = {
            "action": "opened_file",
            "path": path
        }

        self.send_message(
            chat_id,
            (
                "📄 <b>ФАЙЛ</b>\n\n"
                f"📌 Имя: <code>{safe_path}</code>\n\n"
                "📝 <b>Содержимое:</b>\n"
                f"<pre>{safe_content}</pre>"
            ),
            keyboard
        )

    # =====================================================
    # DELETE FILE
    # =====================================================

    def delete_file_start(
        self,
        chat_id,
        user_id,
        path=None
    ):
        if path is None:
            state = self.states.get(
                user_id,
                {}
            )

            path = state.get(
                "path"
            )

        if not path:
            self.send_message(
                chat_id,
                "❌ Файл не выбран."
            )
            return

        self.states[user_id] = {
            "action": "delete_file",
            "path": path
        }

        self.send_message(
            chat_id,
            (
                "🗑 <b>УДАЛЕНИЕ ФАЙЛА</b>\n\n"
                f"Файл: <code>{escape(path)}</code>\n\n"
                "Введите <code>да</code> для подтверждения.\n"
                "Для отмены введите <code>нет</code>."
            )
        )

    # =====================================================
    # EDIT FILE
    # =====================================================

    def edit_file_start(
        self,
        chat_id,
        user_id,
        path=None
    ):
        if path is None:
            state = self.states.get(
                user_id,
                {}
            )

            path = state.get(
                "path"
            )

        if not path:
            self.send_message(
                chat_id,
                "❌ Файл не выбран."
            )
            return

        self.states[user_id] = {
            "action": "edit_file",
            "path": path
        }

        self.send_message(
            chat_id,
            (
                "✏️ <b>РЕДАКТИРОВАНИЕ ФАЙЛА</b>\n\n"
                f"📄 Файл: <code>{escape(path)}</code>\n\n"
                "Отправьте новое содержимое файла.\n\n"
                "⚠️ Старое содержимое будет полностью заменено."
            )
        )

    # =====================================================
    # STATE INPUT
    # =====================================================

    def handle_state_input(
        self,
        chat_id,
        user_id,
        text
    ):
        state = self.states.get(
            user_id
        )

        if not state:
            return False

        action = state.get(
            "action"
        )

        # -------------------------------------------------
        # OPENED FILE
        # -------------------------------------------------

        if action == "opened_file":

            if text == "✏️ Изменить файл":
                self.edit_file_start(
                    chat_id,
                    user_id,
                    state.get("path")
                )
                return True

            if text == "🗑 Удалить файл":
                self.delete_file_start(
                    chat_id,
                    user_id,
                    state.get("path")
                )
                return True

            if text == "⬅️ Назад":
                self.states.pop(
                    user_id,
                    None
                )

                directory = self.get_current_directory(
                    user_id
                )

                self.show_files(
                    chat_id,
                    user_id,
                    directory
                )

                return True

            if text == "🏠 Главная":
                self.states.pop(
                    user_id,
                    None
                )
                return False

            return False

        # -------------------------------------------------
        # DELETE
        # -------------------------------------------------

        if action == "delete_file":

            answer = text.lower().strip()

            if answer not in (
                "да",
                "yes",
                "удалить",
                "нет",
                "no",
                "отмена"
            ):
                self.send_message(
                    chat_id,
                    (
                        "⚠️ Введите <code>да</code> "
                        "для удаления или <code>нет</code> "
                        "для отмены."
                    )
                )
                return True

            if answer in (
                "нет",
                "no",
                "отмена"
            ):
                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    "❌ Удаление отменено."
                )

                return True

            path = state.get(
                "path"
            )

            try:
                self.database.delete_file(
                    user_id,
                    path
                )

                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    f"✅ Файл <b>{escape(path)}</b> удалён."
                )

                directory = self.get_current_directory(
                    user_id
                )

                self.show_files(
                    chat_id,
                    user_id,
                    directory
                )

            except Exception:
                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    "❌ Не удалось удалить файл."
                )

            return True

        # -------------------------------------------------
        # EDIT
        # -------------------------------------------------

        if action == "edit_file":

            path = state.get(
                "path"
            )

            try:
                self.database.update_file(
                    user_id,
                    path,
                    text
                )

                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    (
                        f"✅ Файл <b>{escape(path)}</b> "
                        "обновлён."
                    )
                )

                self.open_file(
                    chat_id,
                    user_id,
                    path
                )

            except Exception:
                self.states.pop(
                    user_id,
                    None
                )

                self.send_message(
                    chat_id,
                    "❌ Не удалось изменить файл."
                )

            return True

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        if action in (
            "create_file",
            "create_folder"
        ):
            return self.handle_input(
                chat_id,
                user_id,
                text
            )

        return False

    # =====================================================
    # BACK
    # =====================================================

    def go_back(
        self,
        chat_id,
        user_id
    ):
        current = self.get_current_directory(
            user_id
        )

        if current == "/":
            self.show_filesystem(
                chat_id,
                user_id
            )
            return

        path = current.rstrip("/")

        if "/" not in path:
            parent = "/"
        else:
            parent = (
                "/"
                + path.rsplit(
                    "/",
                    1
                )[0].strip("/")
                + "/"
            )

        self.set_current_directory(
            user_id,
            parent
        )

        self.show_files(
            chat_id,
            user_id,
            parent
        )

    # =====================================================
    # CANCEL
    # =====================================================

    def cancel(
        self,
        user_id
    ):
        self.states.pop(
            user_id,
            None
        )