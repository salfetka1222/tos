class TOS:
    def __init__(self):
        self.name = "T-OS"
        self.version = "0.1.0"
        self.language = "ru"

    def info(self):
        return {
            "name": self.name,
            "version": self.version,
            "language": self.language,
        }