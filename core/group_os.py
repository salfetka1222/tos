from datetime import datetime


class GroupOS:
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # GROUP INFO
    # ==========================================

    def get_group_info(self, chat_id):
        result = self.bot.request(
            "getChat",
            {
                "chat_id": chat_id
            }
        )

        if not result or not result.get("ok"):
            return None

        return result.get("result")

    # ==========================================
    # MEMBER COUNT
    # ==========================================

    def get_member_count(self, chat_id):
        result = self.bot.request(
            "getChatMemberCount",
            {
                "chat_id": chat_id
            }
        )

        if not result or not result.get("ok"):
            return 0

        return result.get("result", 0)

    # ==========================================
    # ADMINISTRATORS
    # ==========================================

    def get_administrators(self, chat_id):
        result = self.bot.request(
            "getChatAdministrators",
            {
                "chat_id": chat_id
            }
        )

        if not result or not result.get("ok"):
            return []

        return result.get("result", [])

    # ==========================================
    # MEMBERS SCREEN
    # ==========================================

    def render_members(self, chat_id):
        chat = self.get_group_info(chat_id)

        if not chat:
            return "❌ Не удалось получить информацию о группе."

        member_count = self.get_member_count(chat_id)
        administrators = self.get_administrators(chat_id)

        lines = [
            "🖥️ <b>T-OS GROUP OS</b>",
            "",
            "👥 <b>УЧАСТНИКИ ГРУППЫ</b>",
            "",
            f"👥 <b>Всего участников:</b> {member_count}",
            "",
            "👑 <b>АДМИНИСТРАТОРЫ</b>",
            ""
        ]

        if not administrators:
            lines.append("Нет данных об администраторах.")
        else:
            for admin in administrators:
                user = admin.get("user", {})

                user_id = user.get("id")
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                username = user.get("username")

                name = f"{first_name} {last_name}".strip()

                if not name:
                    name = "Без имени"

                if username:
                    display = f"{name} (@{username})"
                else:
                    display = name

                status = admin.get("status", "")

                if status == "creator":
                    role = "👑 Владелец"
                elif status == "administrator":
                    role = "🛡 Администратор"
                else:
                    role = "👤"

                lines.append(
                    f"{role} {display}"
                )

                lines.append(
                    f"   🆔 <code>{user_id}</code>"
                )

        lines.extend([
            "",
            "ℹ️ <i>Telegram не предоставляет ботам полный список участников группы.</i>",
            "📡 <i>Доступны администраторы и общее количество участников.</i>",
            "",
            f"🟢 <b>T-OS:</b> ACTIVE",
            "",
            f"🕐 <b>Обновлено:</b> {datetime.now().strftime('%H:%M:%S')}"
        ])

        return "\n".join(lines)