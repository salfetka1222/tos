from core.user import User
from database.database import Database


class UserManager:
    def __init__(self, database):
        self.database = database

    def create_user(self, user_id, username=None):
        self.database.create_user(user_id, username)

        data = self.database.get_user(user_id)

        return User(
            user_id=data[0],
            username=data[1],
        )

    def get_user(self, user_id):
        data = self.database.get_user(user_id)

        if data is None:
            return None

        return User(
            user_id=data[0],
            username=data[1],
        )