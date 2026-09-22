import sqlite3


class Database:
    def __init__(self, path="tos.db"):
        self.path = path

    def connect(self):
        return sqlite3.connect(self.path)

    def initialize(self):
        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 0
                )
            """)

            connection.commit()

    def create_user(self, user_id, username=None):
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO users
                (user_id, username)
                VALUES (?, ?)
                """,
                (user_id, username)
            )

            connection.commit()

    def get_user(self, user_id):
        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT user_id, username, level, xp, coins
                FROM users
                WHERE user_id = ?
                """,
                (user_id,)
            )

            return cursor.fetchone()