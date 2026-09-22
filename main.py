from telegram.bot import TelegramBot


def main():
    bot = TelegramBot()

    info = bot.get_me()

    if info.get("ok"):
        user = info["result"]

        print("📡 Telegram API: OK")
        print(f"🤖 Бот: @{user.get('username')}")
        print(f"🆔 ID: {user.get('id')}")
    else:
        print("❌ Telegram API: ERROR")
        print(info)


if __name__ == "__main__":
    main()