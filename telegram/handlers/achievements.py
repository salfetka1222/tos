from html import escape


class AchievementsHandler:

    ACHIEVEMENTS = {
        "first_start": {
            "name": "Первый запуск",
            "description": "Ты впервые запустил T-OS.",
            "xp": 10,
            "coins": 5
        },
        "first_file": {
            "name": "Файловый менеджер",
            "description": "Ты создал свой первый файл.",
            "xp": 20,
            "coins": 10
        },
        "first_terminal": {
            "name": "Terminal User",
            "description": "Ты впервые воспользовался Terminal.",
            "xp": 20,
            "coins": 10
        },
        "first_game": {
            "name": "Игрок",
            "description": "Ты сыграл свою первую игру.",
            "xp": 25,
            "coins": 15
        },
        "first_win": {
            "name": "Победитель",
            "description": "Ты одержал первую победу.",
            "xp": 50,
            "coins": 25
        },
        "level_5": {
            "name": "Опытный пользователь",
            "description": "Ты достиг 5 уровня.",
            "xp": 100,
            "coins": 50
        }
    }

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
            return self.bot.request(
                "sendMessage",
                data
            )
        except Exception:
            return None

    def unlock(self, chat_id, user_id, achievement_id):
        achievement = self.ACHIEVEMENTS.get(
            achievement_id
        )

        if not achievement:
            return False

        try:
            already_unlocked = self.database.has_achievement(
                user_id,
                achievement_id
            )
        except Exception:
            already_unlocked = False

        if already_unlocked:
            return False

        try:
            self.database.unlock_achievement(
                user_id,
                achievement_id,
                achievement["name"],
                achievement["description"]
            )
        except Exception:
            return False

        try:
            self.database.add_xp(
                user_id,
                achievement["xp"]
            )
        except Exception:
            pass

        try:
            self.database.add_coins(
                user_id,
                achievement["coins"]
            )
        except Exception:
            pass

        self.send_message(
            chat_id,
            (
                "🏆 <b>НОВОЕ ДОСТИЖЕНИЕ!</b>\n\n"
                f"🎖 <b>{escape(achievement['name'])}</b>\n\n"
                f"{escape(achievement['description'])}\n\n"
                f"✨ +{achievement['xp']} XP\n"
                f"🪙 +{achievement['coins']} монет"
            )
        )

        return True

    def show_achievements(self, chat_id, user_id):
        try:
            unlocked = self.database.get_achievements(
                user_id
            )
        except Exception:
            unlocked = []

        unlocked_ids = set()

        for achievement in unlocked:
            try:
                unlocked_ids.add(
                    achievement["achievement_id"]
                )
            except Exception:
                pass

        result = []

        for achievement_id, achievement in self.ACHIEVEMENTS.items():
            if achievement_id in unlocked_ids:
                icon = "🏆"
                status = "Открыто"
            else:
                icon = "🔒"
                status = "Заблокировано"

            result.append(
                f"{icon} <b>{escape(achievement['name'])}</b>\n"
                f"{escape(achievement['description'])}\n"
                f"Статус: <b>{status}</b>\n"
                f"✨ XP: {achievement['xp']} | "
                f"🪙 {achievement['coins']}"
            )

        keyboard = {
            "keyboard": [
                [
                    {"text": "👤 Мой профиль"}
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
                "🏆 <b>ACHIEVEMENTS OS</b>\n\n"
                + "\n\n".join(result)
            ),
            keyboard
        )

    def handle_button(self, chat_id, user_id, text):
        if text == "🏆 Достижения":
            self.show_achievements(
                chat_id,
                user_id
            )
            return True

        return False