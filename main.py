from core.system import TOS
from core.users import UserManager
from database.database import Database


def main():
    system = TOS()

    database = Database()
    database.initialize()

    users = UserManager(database)

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


if __name__ == "__main__":
    main()