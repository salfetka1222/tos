from core.system import TOS
from core.users import UserManager
from database.database import Database


def main():
    system = TOS()
    users = UserManager()
    database = Database()

    database.initialize()

    user = users.create_user(
        user_id=1,
        username="test_user"
    )

    print("🖥️ T-OS")
    print("=" * 20)

    print(f"Версия: {system.version}")
    print(f"Язык: {system.language}")

    print("\n💾 Database")
    print("SQLite: OK")

    print("\n👤 Пользователь")
    print(f"ID: {user.user_id}")
    print(f"Username: @{user.username}")
    print(f"Уровень: {user.level}")
    print(f"XP: {user.xp}")
    print(f"Монеты: {user.coins}")


if __name__ == "__main__":
    main()
