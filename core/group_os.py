import sqlite3
from datetime import datetime


class GroupOS:
    """
    Group OS для T-OS.

    Отвечает за:
    - настройки групп;
    - статистику;
    - действия модерации;
    - права;
    - Group Audit Log;
    - настройки ИИ;
    - отображение участников.
    """

    def __init__(self, bot, database=None):
        self.bot = bot
        self.database = database

        # Используем БД T-OS, если она передана.
        # Это позволяет Group OS работать с той же SQLite БД,
        # что и остальные компоненты системы.
        if database:
            self.db_path = getattr(
                database,
                "db_path",
                getattr(database, "path", "tos.db")
            )
        else:
            self.db_path = "tos.db"

        self.init_database()

    # =========================================================
    # DATABASE
    # =========================================================

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id TEXT PRIMARY KEY,
                ai_enabled INTEGER NOT NULL DEFAULT 1,
                ai_mode TEXT NOT NULL DEFAULT 'normal',
                moderation_enabled INTEGER NOT NULL DEFAULT 1,
                welcome_enabled INTEGER NOT NULL DEFAULT 0,
                log_enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_statistics (
                chat_id TEXT PRIMARY KEY,
                messages INTEGER NOT NULL DEFAULT 0,
                commands INTEGER NOT NULL DEFAULT 0,
                moderation_actions INTEGER NOT NULL DEFAULT 0,
                ai_requests INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS group_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                target_id TEXT,
                details TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_group_audit_chat
            ON group_audit_log(chat_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_group_audit_created
            ON group_audit_log(created_at)
        """)

        conn.commit()
        conn.close()

    # =========================================================
    # GROUP SETTINGS
    # =========================================================

    def ensure_group(self, chat_id):
        chat_id = str(chat_id)
        now = datetime.utcnow().isoformat()

        conn = self.get_connection()

        conn.execute("""
            INSERT OR IGNORE INTO group_settings
            (
                chat_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?)
        """, (chat_id, now, now))

        conn.execute("""
            INSERT OR IGNORE INTO group_statistics
            (
                chat_id,
                updated_at
            )
            VALUES (?, ?)
        """, (chat_id, now))

        conn.commit()
        conn.close()

    def get_settings(self, chat_id):
        self.ensure_group(chat_id)

        conn = self.get_connection()

        row = conn.execute("""
            SELECT *
            FROM group_settings
            WHERE chat_id = ?
        """, (str(chat_id),)).fetchone()

        conn.close()

        return dict(row) if row else None

    def update_setting(self, chat_id, setting, value):
        allowed = {
            "ai_enabled",
            "ai_mode",
            "moderation_enabled",
            "welcome_enabled",
            "log_enabled",
        }

        if setting not in allowed:
            return False

        self.ensure_group(chat_id)

        now = datetime.utcnow().isoformat()

        conn = self.get_connection()

        conn.execute(
            f"""
            UPDATE group_settings
            SET {setting} = ?,
                updated_at = ?
            WHERE chat_id = ?
            """,
            (
                value,
                now,
                str(chat_id)
            )
        )

        conn.commit()
        conn.close()

        return True

    def toggle_ai(self, chat_id):
        settings = self.get_settings(chat_id)

        if not settings:
            return False

        new_value = 0 if settings["ai_enabled"] else 1

        self.update_setting(
            chat_id,
            "ai_enabled",
            new_value
        )

        return bool(new_value)

    def toggle_moderation(self, chat_id):
        settings = self.get_settings(chat_id)

        if not settings:
            return False

        new_value = 0 if settings["moderation_enabled"] else 1

        self.update_setting(
            chat_id,
            "moderation_enabled",
            new_value
        )

        return bool(new_value)

    # =========================================================
    # STATISTICS
    # =========================================================

    def increment_stat(
        self,
        chat_id,
        stat,
        amount=1
    ):
        allowed = {
            "messages",
            "commands",
            "moderation_actions",
            "ai_requests",
        }

        if stat not in allowed:
            return False

        self.ensure_group(chat_id)

        now = datetime.utcnow().isoformat()

        conn = self.get_connection()

        conn.execute(
            f"""
            UPDATE group_statistics
            SET {stat} = {stat} + ?,
                updated_at = ?
            WHERE chat_id = ?
            """,
            (
                amount,
                now,
                str(chat_id)
            )
        )

        conn.commit()
        conn.close()

        return True

    def get_statistics(self, chat_id):
        self.ensure_group(chat_id)

        conn = self.get_connection()

        row = conn.execute("""
            SELECT *
            FROM group_statistics
            WHERE chat_id = ?
        """, (str(chat_id),)).fetchone()

        conn.close()

        if row:
            return dict(row)

        return {
            "chat_id": str(chat_id),
            "messages": 0,
            "commands": 0,
            "moderation_actions": 0,
            "ai_requests": 0,
        }

    # =========================================================
    # AUDIT LOG
    # =========================================================

    def audit(
        self,
        chat_id,
        action,
        user_id=None,
        target_id=None,
        details=None
    ):
        settings = self.get_settings(chat_id)

        if settings and not settings["log_enabled"]:
            return False

        conn = self.get_connection()

        conn.execute("""
            INSERT INTO group_audit_log
            (
                chat_id,
                user_id,
                action,
                target_id,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(chat_id),
            str(user_id) if user_id is not None else None,
            action,
            str(target_id) if target_id is not None else None,
            details,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        return True

    def get_audit_log(
        self,
        chat_id,
        limit=50
    ):
        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 50

        conn = self.get_connection()

        rows = conn.execute("""
            SELECT *
            FROM group_audit_log
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (
            str(chat_id),
            limit
        )).fetchall()

        conn.close()

        return [dict(row) for row in rows]

    def clear_audit_log(self, chat_id):
        conn = self.get_connection()

        cursor = conn.execute("""
            DELETE FROM group_audit_log
            WHERE chat_id = ?
        """, (str(chat_id),))

        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted

    # =========================================================
    # MEMBERS
    # =========================================================

    def render_members(self, chat_id):
        """
        Отображает доступную информацию об участниках группы.

        Telegram Bot API не позволяет боту получить полный
        список обычных участников группы, поэтому здесь
        показываются администраторы и общее количество участников.
        """

        members_response = self.get_administrators(chat_id)
        count_response = self.get_member_count(chat_id)

        if not members_response or not members_response.get("ok"):
            return "❌ Telegram не вернул список администраторов."

        admins = members_response.get("result", [])

        if count_response and count_response.get("ok"):
            count = count_response.get("result", "?")
        else:
            count = "?"

        lines = [
            "👥 <b>УЧАСТНИКИ ГРУППЫ</b>",
            "",
            f"👤 Всего участников: <b>{count}</b>",
            f"🛡 Администраторов: <b>{len(admins)}</b>",
            ""
        ]

        for member in admins:
            user = member.get("user", {})

            user_id = user.get("id", "?")
            username = user.get("username")

            name = (
                user.get("first_name")
                or user.get("last_name")
                or "Без имени"
            )

            if username:
                label = f"@{username}"
            else:
                label = name

            if member.get("status") == "creator":
                status = "👑 Владелец"
            else:
                status = "🛡 Администратор"

            lines.append(
                f"{status} {label} <code>{user_id}</code>"
            )

        lines.extend([
            "",
            "ℹ️ Telegram Bot API не предоставляет боту "
            "полный список обычных участников.",
            "Здесь отображаются доступные администраторы "
            "и общее число участников."
        ])

        return "\n".join(lines)

    # =========================================================
    # TELEGRAM API
    # =========================================================

    def get_chat(self, chat_id):
        return self.bot.request(
            "getChat",
            {
                "chat_id": chat_id
            }
        )

    def get_member_count(self, chat_id):
        return self.bot.request(
            "getChatMemberCount",
            {
                "chat_id": chat_id
            }
        )

    def get_member(self, chat_id, user_id):
        return self.bot.request(
            "getChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id
            }
        )

    def get_administrators(self, chat_id):
        return self.bot.request(
            "getChatAdministrators",
            {
                "chat_id": chat_id
            }
        )

    # =========================================================
    # PERMISSIONS
    # =========================================================

    def get_user_status(
        self,
        chat_id,
        user_id
    ):
        response = self.get_member(
            chat_id,
            user_id
        )

        if not response or not response.get("ok"):
            return None

        result = response.get("result", {})

        return result.get("status")

    def is_admin(
        self,
        chat_id,
        user_id
    ):
        status = self.get_user_status(
            chat_id,
            user_id
        )

        return status in (
            "creator",
            "administrator"
        )

    # =========================================================
    # MODERATION
    # =========================================================

    def restrict_member(
        self,
        chat_id,
        user_id,
        permissions
    ):
        settings = self.get_settings(chat_id)

        if settings and not settings["moderation_enabled"]:
            return {
                "ok": False,
                "error": "moderation_disabled"
            }

        response = self.bot.request(
            "restrictChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id,
                "permissions": permissions
            }
        )

        if response and response.get("ok"):
            self.increment_stat(
                chat_id,
                "moderation_actions"
            )

            self.audit(
                chat_id,
                "member_restricted",
                target_id=user_id
            )

        return response

    def unrestrict_member(
        self,
        chat_id,
        user_id
    ):
        permissions = {
            "can_send_messages": True,
            "can_send_audios": True,
            "can_send_documents": True,
            "can_send_photos": True,
            "can_send_videos": True,
            "can_send_video_notes": True,
            "can_send_voice_notes": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True
        }

        return self.restrict_member(
            chat_id,
            user_id,
            permissions
        )

    def ban_member(
        self,
        chat_id,
        user_id
    ):
        settings = self.get_settings(chat_id)

        if settings and not settings["moderation_enabled"]:
            return {
                "ok": False,
                "error": "moderation_disabled"
            }

        response = self.bot.request(
            "banChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id
            }
        )

        if response and response.get("ok"):
            self.increment_stat(
                chat_id,
                "moderation_actions"
            )

            self.audit(
                chat_id,
                "member_banned",
                target_id=user_id
            )

        return response

    def unban_member(
        self,
        chat_id,
        user_id
    ):
        response = self.bot.request(
            "unbanChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id,
                "only_if_banned": False
            }
        )

        if response and response.get("ok"):
            self.increment_stat(
                chat_id,
                "moderation_actions"
            )

            self.audit(
                chat_id,
                "member_unbanned",
                target_id=user_id
            )

        return response