from core.system import TOS


def main():
    system = TOS()

    print("🖥️ T-OS")
    print("=" * 20)

    info = system.info()

    print(f"Название: {info['name']}")
    print(f"Версия: {info['version']}")
    print(f"Язык: {info['language']}")
    print(f"Среда: {info['environment']}")
    print(f"Debug: {info['debug']}")


if __name__ == "__main__":
    main()
