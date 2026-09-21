from core.system import TOS
from core.users import UserManager


def main():
    system = TOS()
    users = UserManager()

    user = users.create_user(
        user_id=1,
        username="test_user"
    )

    print("🖥️ T-OS")
    print("=" * 20)

    print(f"Версия: {system.version}")
    print(f"Язык: {system.language}")

    print("\n👤 Пользователь")
    print(f"ID: {user.user_id}")
    print(f"Username: @{user.username}")
    print(f"Уровень: {user.level}")
    print(f"XP: {user.xp}")
    print(f"Монеты: {user.coins}")

    print(f"\nВсего пользователей: {users.count()}")


if __name__ == "__main__":
    main()
