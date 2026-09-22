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

            connection.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    file_type TEXT NOT NULL DEFAULT 'file',
                    content TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, path)
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

    def create_file(self, user_id, path, file_type="file", content=""):
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO files
                (user_id, path, file_type, content)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, path, file_type, content)
            )

            connection.commit()

    def get_file(self, user_id, path):
        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT id, path, file_type, content
                FROM files
                WHERE user_id = ? AND path = ?
                """,
                (user_id, path)
            )

            return cursor.fetchone()

    def get_files(self, user_id, directory):
        prefix = directory.rstrip("/") + "/"

        with self.connect() as connection:
            cursor = connection.execute(
                """
                SELECT id, path, file_type, content
                FROM files
                WHERE user_id = ?
                AND path LIKE ?
                ORDER BY file_type DESC, path ASC
                """,
                (user_id, prefix + "%")
            )

            return cursor.fetchall()

    def update_file(self, user_id, path, content):
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE files
                SET content = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND path = ?
                """,
                (content, user_id, path)
            )

            connection.commit()

    def delete_file(self, user_id, path):
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE files
                SET path = ?
                WHERE user_id = ? AND path = ?
                """,
                (
                    "/home/user/Trash/" + path.split("/")[-1],
                    user_id,
                    path
                )
            )

            connection.commit()