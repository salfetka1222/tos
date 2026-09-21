from core.system import TOS


def main():
    system = TOS()

    print(f"🖥️ {system.name}")
    print(f"Версия: {system.version}")
    print(f"Язык: {system.language}")


if __name__ == "__main__":
    main()
