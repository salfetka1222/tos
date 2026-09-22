from html import escape


class ProfileHandler:

    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

    def send_message(self, chat_id, text, reply_markup=None):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        if reply_markup:
            data["reply_markup"] = reply_markup

        try:
            return self.bot.request("sendMessage", data)
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return self.database.get_user(user_id)
        except Exception:
            return None

    def show_profile(self, chat_id, user_id):
        user = self.get_user(user_id)

        if not user:
            self.send_message(
                chat_id,
                (
                    "❌ <b>Профиль не найден</b>\n\n"
                    "Попробуйте отправить /start."
                )
            )
            return

        try:
            username = user["username"] or "не указан"
        except Exception:
            username = "не указан"

        try:
            level = user["level"]
        except Exception:
            level = 1

        try:
            xp = user["xp"]
        except Exception:
            xp = 0

        try:
            coins = user["coins"]
        except Exception:
            coins = 0

        try:
            games_played = user["games_played"]
        except Exception:
            games_played = 0

        try:
            games_won = user["games_won"]
        except Exception:
            games_won = 0

        try:
            commands = user["commands"]
        except Exception:
            commands = 0

        try:
            created_at = user["created_at"] or "неизвестно"
        except Exception:
            created_at = "неизвестно"

        try:
            achievements = self.database.get_achievements(user_id)
        except Exception:
            achievements = []

        achievement_count = len(achievements)

        keyboard = {
            "keyboard": [
                [
                    {"text": "🏆 Достижения"},
                    {"text": "🔄 Обновить профиль"}
                ],
                [
                    {"text": "🏠 Главная"}
                ]
            ],
            "resize_keyboard": True
        }

        text = (
            "👤 <b>T-OS PROFILE</b>\n\n"

            f"🆔 ID: <code>{escape(str(user_id))}</code>\n"
            f"👤 Username: <b>@{escape(str(username))}</b>\n\n"

            "📊 <b>Статистика</b>\n"
            f"⭐ Уровень: <b>{level}</b>\n"
            f"✨ XP: <b>{xp}</b>\n"
            f"🪙 Монеты: <b>{coins}</b>\n"
            f"🎮 Игр сыграно: <b>{games_played}</b>\n"
            f"🏆 Побед: <b>{games_won}</b>\n"
            f"⌨️ Команд: <b>{commands}</b>\n\n"

            "🏅 <b>Достижения</b>\n"
            f"Открыто: <b>{achievement_count}</b>\n\n"

            "📅 <b>Дата регистрации</b>\n"
            f"<code>{escape(str(created_at))}</code>"
        )

        self.send_message(
            chat_id,
            text,
            keyboard
        )

    def show_achievements(self, chat_id, user_id):
        try:
            achievements = self.database.get_achievements(user_id)
        except Exception:
            achievements = []

        if not achievements:
            self.send_message(
                chat_id,
                (
                    "🏆 <b>ДОСТИЖЕНИЯ</b>\n\n"
                    "Пока нет открытых достижений.\n\n"
                    "Продолжайте пользоваться T-OS!"
                )
            )
            return

        result = []

        for achievement in achievements:
            try:
                name = achievement["name"]
            except Exception:
                name = "Без названия"

            try:
                description = achievement["description"]
            except Exception:
                description = ""

            result.append(
                "🏆 <b>"
                + escape(str(name))
                + "</b>\n"
                + escape(str(description))
            )

        self.send_message(
            chat_id,
            (
                "🏆 <b>ДОСТИЖЕНИЯ</b>\n\n"
                + "\n\n".join(result)
            )
        )

    def handle_button(self, chat_id, user_id, text):
        if text == "👤 Мой профиль":
            self.show_profile(chat_id, user_id)
            return True

        if text == "🏆 Достижения":
            self.show_achievements(chat_id, user_id)
            return True

        if text == "🔄 Обновить профиль":
            self.show_profile(chat_id, user_id)
            return True

        return False