from core.user import User


class UserManager:
    def __init__(self):
        self.users = {}

    def create_user(self, user_id, username=None):
        if user_id in self.users:
            return self.users[user_id]

        user = User(user_id, username)
        self.users[user_id] = user

        return user

    def get_user(self, user_id):
        return self.users.get(user_id)

    def delete_user(self, user_id):
        if user_id in self.users:
            del self.users[user_id]

    def count(self):
        return len(self.users)
