class User:
    def __init__(self, user_id, username=None):
        self.user_id = user_id
        self.username = username
        self.level = 1
        self.xp = 0
        self.coins = 0

    def add_xp(self, amount):
        self.xp += amount

    def add_coins(self, amount):
        self.coins += amount

    def info(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "level": self.level,
            "xp": self.xp,
            "coins": self.coins,
        }
