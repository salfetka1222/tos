from datetime import datetime, timezone


class GroupOS:
    """
    Group OS — системный слой управления Telegram-группами.

    Первый этап:
    - Group Dashboard
    - базовая информация о группе
    - информация о создателе/администраторах
    - количество участников
    - статус T-OS
    """

    def __init__(self, bot):
        self.bot = bot

    async def get_dashboard(self, chat_id: int) -> dict:
        """Получить данные Group Dashboard."""

        chat = await self.bot.get_chat(chat_id)

        members_count = None

        try:
            members_count = await self.bot.get_chat_member_count(chat_id)
        except Exception:
            pass

        return {
            "chat_id": chat.id,
            "title": getattr(chat, "title", "Unknown"),
            "type": getattr(chat, "type", "unknown"),
            "username": getattr(chat, "username", None),
            "members_count": members_count,
            "tos_status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def render_dashboard(self, chat_id: int) -> str:
        """Сформировать текст Group Dashboard."""

        data = await self.get_dashboard(chat_id)

        chat_type = {
            "group": "Группа",
            "supergroup": "Супергруппа",
            "channel": "Канал",
        }.get(data["type"], data["type"])

        username = (
            f"@{data['username']}"
            if data["username"]
            else "нет"
        )

        members = (
            str(data["members_count"])
            if data["members_count"] is not None
            else "недоступно"
        )

        return (
            "🖥 <b>Group OS</b>\n\n"
            "🏠 <b>Group Dashboard</b>\n\n"
            f"📌 <b>Название:</b> {data['title']}\n"
            f"🆔 <b>ID:</b> <code>{data['chat_id']}</code>\n"
            f"💬 <b>Тип:</b> {chat_type}\n"
            f"🔗 <b>Username:</b> {username}\n"
            f"👥 <b>Участников:</b> {members}\n\n"
            "🟢 <b>T-OS:</b> активна\n\n"
            "⚙️ <b>Group OS</b>\n"
            "├ 👥 Members\n"
            "├ 🛡 Moderation\n"
            "├ 📜 Group Audit Log\n"
            "├ ⚙️ Permissions\n"
            "├ 🤖 AI Settings\n"
            "└ 📊 Statistics"
        )