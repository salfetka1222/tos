import sqlite3


class Database:

    def __init__(self, path="tos.db"):
        self.path = path

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):

        with self.connect() as connection:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 0,
                    commands INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

            connection.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, achievement)
                )
            """)

            # =============================================
            # AUDIT LOG
            # =============================================

            connection.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    target_id INTEGER,
                    details TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.commit()

            self._migrate_users(connection)

    # =====================================================
    # MIGRATIONS
    # =====================================================

    def _migrate_users(self, connection):

        cursor = connection.execute(
            "PRAGMA table_info(users)"
        )

        columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        migrations = {
            "commands": "INTEGER DEFAULT 0",
            "games_played": "INTEGER DEFAULT 0",
            "games_won": "INTEGER DEFAULT 0",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        for column, definition in migrations.items():

            if column not in columns:

                connection.execute(
                    f"""
                    ALTER TABLE users
                    ADD COLUMN {column} {definition}
                    """
                )

        connection.commit()

    # =====================================================
    # USERS
    # =====================================================

    def create_user(
        self,
        user_id,
        username=None
    ):

        with self.connect() as connection:

            connection.execute(
                """
                INSERT OR IGNORE INTO users
                (user_id, username)
                VALUES (?, ?)
                """,
                (
                    user_id,
                    username
                )
            )

            connection.execute(
                """
                UPDATE users
                SET username = ?
                WHERE user_id = ?
                """,
                (
                    username,
                    user_id
                )
            )

            connection.commit()

    def get_user(self, user_id):

        with self.connect() as connection:

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
                WHERE user_id = ?
                """,
                (user_id,)
            )

            return cursor.fetchone()

    # =====================================================
    # XP / LEVEL
    # =====================================================

    def add_xp(
        self,
        user_id,
        amount
    ):

        if amount <= 0:
            return

        with self.connect() as connection:

            connection.execute(
                """
                UPDATE users
                SET xp = xp + ?
                WHERE user_id = ?
                """,
                (
                    amount,
                    user_id
                )
            )

            connection.commit()

        self.update_level(user_id)

    def update_level(self, user_id):

        with self.connect() as connection:

            user = connection.execute(
                """
                SELECT xp, level
                FROM users
                WHERE user_id = ?
                """,
                (user_id,)
            ).fetchone()

            if not user:
                return

            xp = user["xp"]
            current_level = user["level"]

            new_level = max(
                1,
                (xp // 100) + 1
            )

            if new_level != current_level:

                connection.execute(
                    """
                    UPDATE users
                    SET level = ?
                    WHERE user_id = ?
                    """,
                    (
                        new_level,
                        user_id
                    )
                )

                connection.commit()

    # =====================================================
    # COINS
    # =====================================================

    def add_coins(
        self,
        user_id,
        amount
    ):

        with self.connect() as connection:

            connection.execute(
                """
                UPDATE users
                SET coins = coins + ?
                WHERE user_id = ?
                """,
                (
                    amount,
                    user_id
                )
            )

            connection.commit()

    def remove_coins(
        self,
        user_id,
        amount
    ):

        if amount <= 0:
            return False

        with self.connect() as connection:

            user = connection.execute(
                """
                SELECT coins
                FROM users
                WHERE user_id = ?
                """,
                (user_id,)
            ).fetchone()

            if not user:
                return False

            if user["coins"] < amount:
                return False

            connection.execute(
                """
                UPDATE users
                SET coins = coins - ?
                WHERE user_id = ?
                """,
                (
                    amount,
                    user_id
                )
            )

            connection.commit()

            return True

    # =====================================================
    # COMMANDS
    # =====================================================

    def increment_commands(self, user_id):

        with self.connect() as connection:

            connection.execute(
                """
                UPDATE users
                SET commands = commands + 1
                WHERE user_id = ?
                """,
                (user_id,)
            )

            connection.commit()

    # =====================================================
    # GAMES
    # =====================================================

    def increment_games(
        self,
        user_id,
        won=False
    ):

        with self.connect() as connection:

            connection.execute(
                """
                UPDATE users
                SET games_played = games_played + 1
                WHERE user_id = ?
                """,
                (user_id,)
            )

            if won:

                connection.execute(
                    """
                    UPDATE users
                    SET games_won = games_won + 1
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )

            connection.commit()

    # =====================================================
    # ACHIEVEMENTS
    # =====================================================

    def unlock_achievement(
        self,
        user_id,
        achievement
    ):

        with self.connect() as connection:

            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO achievements
                (user_id, achievement)
                VALUES (?, ?)
                """,
                (
                    user_id,
                    achievement
                )
            )

            connection.commit()

            return cursor.rowcount > 0

    def has_achievement(
        self,
        user_id,
        achievement
    ):

        with self.connect() as connection:

            cursor = connection.execute(
                """
                SELECT id
                FROM achievements
                WHERE user_id = ?
                AND achievement = ?
                """,
                (
                    user_id,
                    achievement
                )
            )

            return cursor.fetchone() is not None

    def get_achievements(
        self,
        user_id
    ):

        with self.connect() as connection:

            cursor = connection.execute(
                """
                SELECT
                    achievement,
                    unlocked_at
                FROM achievements
                WHERE user_id = ?
                ORDER BY unlocked_at ASC
                """,
                (user_id,)
            )

            return cursor.fetchall()

    # =====================================================
    # FILES
    # =====================================================

    def create_file(
        self,
        user_id,
        path,
        file_type="file",
        content=""
    ):

        with self.connect() as connection:

            connection.execute(
                """
                INSERT OR IGNORE INTO files
                (user_id, path, file_type, content)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    path,
                    file_type,
                    content
                )
            )

            connection.commit()

    def get_file(
        self,
        user_id,
        path
    ):

        with self.connect() as connection:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    path,
                    file_type,
                    content
                FROM files
                WHERE user_id = ?
                AND path = ?
                """,
                (
                    user_id,
                    path
                )
            )

            return cursor.fetchone()

    def get_files(
        self,
        user_id,
        directory
    ):

        prefix = directory.rstrip("/") + "/"

        with self.connect() as connection:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    path,
                    file_type,
                    content
                FROM files
                WHERE user_id = ?
                AND path LIKE ?
                ORDER BY file_type DESC, path ASC
                """,
                (
                    user_id,
                    prefix + "%"
                )
            )

            return cursor.fetchall()

    def update_file(
        self,
        user_id,
        path,
        content
    ):

        with self.connect() as connection:

            connection.execute(
                """
                UPDATE files
                SET
                    content = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                AND path = ?
                """,
                (
                    content,
                    user_id,
                    path
                )
            )

            connection.commit()

    def delete_file(
        self,
        user_id,
        path
    ):

        with self.connect() as connection:

            connection.execute(
                """
                DELETE FROM files
                WHERE user_id = ?
                AND path = ?
                """,
                (
                    user_id,
                    path
                )
            )

            connection.commit()

    def path_exists(
        self,
        user_id,
        path
    ):

        return self.get_file(
            user_id,
            path
        ) is not None

    # =====================================================
    # AUDIT LOG
    # =====================================================

    def add_audit_log(
        self,
        actor_id,
        action,
        target_id=None,
        details=""
    ):

        with self.connect() as connection:

            connection.execute(
                """
                INSERT INTO audit_log
                (
                    actor_id,
                    action,
                    target_id,
                    details
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    actor_id,
                    action,
                    target_id,
                    details
                )
            )

            connection.commit()

    def get_audit_logs(
        self,
        limit=20
    ):

        limit = max(
            1,
            min(int(limit), 100)
        )

        with self.connect() as connection:

            cursor = connection.execute(
                """
                SELECT
                    id,
                    actor_id,
                    action,
                    target_id,
                    details,
                    created_at
                FROM audit_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

            return cursor.fetchall()