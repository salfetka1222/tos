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
    # MAIN FILESYSTEM
    # =====================================================

    def show_filesystem(
        self,
        chat_id,
        user_id
    ):
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
        directory="/"
    ):
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
            f"📍 Путь: <code>{directory}</code>",
            ""
        ]

        if not files:
            lines.append(
                "📭 В этой папке пока ничего нет."
            )

        else:
            for file in files:
                path = file.get(
                    "path",
                    ""
                )

                file_type = file.get(
                    "file_type",
                    "file"
                )

                name = path.rstrip("/").split("/")[-1]

                if not name:
                    name = path

                if file_type == "folder":
                    icon = "📁"
                else:
                    icon = "📄"

                lines.append(
                    f"{icon} <code>{name}</code>"
                )

        keyboard = {
            "keyboard": [
                [
                    {"text": "📄 Создать файл"},
                    {"text": "📁 Создать папку"}
                ],
                [
                    {"text": "🔄 Обновить"}
                ],
                [
                    {"text": "⬅️ Назад"}
                ]
            ],
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
        self.states[user_id] = {
            "action": "create_file"
        }

        self.send_message(
            chat_id,
            (
                "📄 <b>СОЗДАНИЕ ФАЙЛА</b>\n\n"
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
        self.states[user_id] = {
            "action": "create_folder"
        }

        self.send_message(
            chat_id,
            (
                "📁 <b>СОЗДАНИЕ ПАПКИ</b>\n\n"
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
        state = self.states.get(user_id)

        if not state:
            return False

        text = text.strip()

        if not text:
            self.send_message(
                chat_id,
                "❌ Имя не может быть пустым."
            )
            return True

        action = state.get("action")

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

            try:
                if self.database.path_exists(
                    user_id,
                    text
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
                    text,
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
                        f"✅ Файл <b>{text}</b> создан.\n\n"
                        "📄 Содержимое пока пустое."
                    )
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

            try:
                path = text.rstrip("/") + "/"

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
                    f"✅ Папка <b>{text}</b> создана."
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

        file_type = file.get(
            "file_type",
            "file"
        )

        if file_type == "folder":
            self.show_files(
                chat_id,
                user_id,
                path
            )
            return

        content = file.get(
            "content",
            ""
        )

        if not content:
            content = "📭 Файл пуст."

        if len(content) > 3500:
            content = content[:3500] + "\n\n..."

        keyboard = {
            "keyboard": [
                [
                    {"text": "✏️ Изменить файл"},
                    {"text": "🗑 Удалить файл"}
                ],
                [
                    {"text": "⬅️ Назад"}
                ]
            ],
            "resize_keyboard": True
        }

        self.send_message(
            chat_id,
            (
                "📄 <b>ФАЙЛ</b>\n\n"
                f"📌 Имя: <code>{path}</code>\n\n"
                "📝 <b>Содержимое:</b>\n"
                f"<pre>{content}</pre>"
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
        path
    ):
        self.states[user_id] = {
            "action": "delete_file",
            "path": path
        }

        self.send_message(
            chat_id,
            (
                "🗑 <b>УДАЛЕНИЕ ФАЙЛА</b>\n\n"
                f"Файл: <code>{path}</code>\n\n"
                "Введите <code>да</code> для подтверждения."
            )
        )

    # =====================================================
    # EDIT FILE
    # =====================================================

    def edit_file_start(
        self,
        chat_id,
        user_id,
        path
    ):
        self.states[user_id] = {
            "action": "edit_file",
            "path": path
        }

        self.send_message(
            chat_id,
            (
                "✏️ <b>РЕДАКТИРОВАНИЕ ФАЙЛА</b>\n\n"
                f"📄 Файл: <code>{path}</code>\n\n"
                "Отправьте новое содержимое файла."
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
        state = self.states.get(user_id)

        if not state:
            return False

        action = state.get("action")

        # -------------------------------------------------
        # DELETE
        # -------------------------------------------------

        if action == "delete_file":

            if text.lower() not in (
                "да",
                "yes",
                "удалить"
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
                    f"✅ Файл <b>{path}</b> удалён."
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
                    f"✅ Файл <b>{path}</b> обновлён."
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

        return self.handle_input(
            chat_id,
            user_id,
            text
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