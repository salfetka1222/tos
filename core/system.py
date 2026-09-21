from core.config import Config


class TOS:
    def __init__(self):
        self.name = Config.APP_NAME
        self.version = Config.VERSION
        self.language = Config.DEFAULT_LANGUAGE
        self.environment = Config.ENVIRONMENT
        self.debug = Config.DEBUG

    def info(self):
        return {
            "name": self.name,
            "version": self.version,
            "language": self.language,
            "environment": self.environment,
            "debug": self.debug,
        }
