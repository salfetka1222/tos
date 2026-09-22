import os


class DeveloperSystem:

    def __init__(self, database):
        self.database = database

        developer_id = os.getenv("TOS_DEVELOPER_ID")

        try:
            self.developer_id = int(developer_id)
        except (TypeError, ValueError):
            self.developer_id = None

    def is_developer(self, user_id):
        if self.developer_id is None:
            return False

        return int(user_id) == self.developer_id

    def get_system_info(self):
        with self.database.connect() as connection:

            users = connection.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            files = connection.execute(
                "SELECT COUNT(*) FROM files"
            ).fetchone()[0]

            achievements = connection.execute(
                "SELECT COUNT(*) FROM achievements"
            ).fetchone()[0]

        return {
            "users": users,
            "files": files,
            "achievements": achievements
        }

    def get_user(self, user_id):
        return self.database.get_user(user_id)

    def get_users(self, limit=20):
        limit = max(1, min(int(limit), 100))

        with self.database.connect() as connection:

            cursor = connection.execute(
                """
                SELECT
                    user_id,
                    username,
                    level,
                    xp,
                    coins,
                    commands,
                    games_played,
                    games_won,
                    created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )

            return cursor.fetchall()