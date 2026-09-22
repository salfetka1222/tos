import random


class GamesSystem:
    def __init__(self, database):
        self.database = database

        # Состояние активных игр
        self.active_games = {}

        # Вопросы для Quiz
        self.quiz_questions = [
            {
                "question": "Как называется операционная система T-OS?",
                "answers": ["t-os", "tos", "t os"],
                "reward": 15
            },
            {
                "question": "Какая база данных используется T-OS?",
                "answers": ["sqlite", "sqlite3"],
                "reward": 15
            },
            {
                "question": "На какой платформе работает T-OS?",
                "answers": ["telegram"],
                "reward": 15
            }
        ]

        # Загадки
        self.riddles = [
            {
                "question": "Что имеет клавиши, но не открывает двери?",
                "answers": ["клавиатура"],
                "reward": 15
            },
            {
                "question": "Что можно увидеть с закрытыми глазами?",
                "answers": ["сон", "сны"],
                "reward": 15
            },
            {
                "question": "Что идёт, но никогда не ходит?",
                "answers": ["часы", "время"],
                "reward": 15
            }
        ]

    # =========================================================
    # START
    # =========================================================

    def start_dice(self, user_id):
        result = random.randint(1, 6)

        # 4-6 = победа
        won = result >= 4

        self.finish_game(
            user_id,
            won,
            xp=10,
            coins=10 if won else 2
        )

        return result, won

    def start_guess(self, user_id):
        number = random.randint(1, 10)

        self.active_games[user_id] = {
            "type": "guess",
            "number": number,
            "attempts": 0
        }

        return (
            "🔢 GUESS NUMBER\n\n"
            "Я загадал число от 1 до 10.\n"
            "Попробуй угадать!"
        )

    def check_guess(self, user_id, answer):
        game = self.active_games.get(user_id)

        if not game or game["type"] != "guess":
            return None

        try:
            number = int(answer)
        except ValueError:
            return {
                "message": "❌ Введи целое число от 1 до 10.",
                "finished": False
            }

        if number < 1 or number > 10:
            return {
                "message": "❌ Число должно быть от 1 до 10.",
                "finished": False
            }

        game["attempts"] += 1

        target = game["number"]

        if number == target:
            attempts = game["attempts"]

            self.active_games.pop(user_id, None)

            self.finish_game(
                user_id,
                True,
                xp=20,
                coins=20
            )

            return {
                "message": (
                    "🎉 Правильно!\n\n"
                    f"Число: {target}\n"
                    f"Попыток: {attempts}\n\n"
                    "⭐ +20 XP\n"
                    "🪙 +20 T-Coins"
                ),
                "finished": True
            }

        if number < target:
            hint = "больше"
        else:
            hint = "меньше"

        if game["attempts"] >= 5:
            self.active_games.pop(user_id, None)

            self.finish_game(
                user_id,
                False,
                xp=5,
                coins=2
            )

            return {
                "message": (
                    "😔 Попытки закончились.\n\n"
                    f"Я загадал: {target}\n\n"
                    "⭐ +5 XP\n"
                    "🪙 +2 T-Coins"
                ),
                "finished": True
            }

        return {
            "message": (
                f"❌ Не угадал.\n"
                f"Попробуй число {hint}.\n\n"
                f"Попытка: {game['attempts']}/5"
            ),
            "finished": False
        }

    # =========================================================
    # QUIZ
    # =========================================================

    def start_quiz(self, user_id):
        question = random.choice(
            self.quiz_questions
        )

        self.active_games[user_id] = {
            "type": "quiz",
            "question": question
        }

        return (
            "🧠 QUIZ\n\n"
            f"{question['question']}\n\n"
            "Напиши ответ."
        )

    def check_quiz(self, user_id, answer):
        game = self.active_games.get(user_id)

        if not game or game["type"] != "quiz":
            return None

        question = game["question"]

        answer = answer.strip().lower()

        correct = answer in [
            item.lower()
            for item in question["answers"]
        ]

        self.active_games.pop(
            user_id,
            None
        )

        if correct:
            reward = question["reward"]

            self.finish_game(
                user_id,
                True,
                xp=reward,
                coins=reward
            )

            return {
                "message": (
                    "🎉 Правильно!\n\n"
                    f"⭐ +{reward} XP\n"
                    f"🪙 +{reward} T-Coins"
                ),
                "finished": True
            }

        self.finish_game(
            user_id,
            False,
            xp=5,
            coins=2
        )

        return {
            "message": (
                "❌ Неправильно.\n\n"
                f"Правильный ответ: "
                f"{question['answers'][0]}\n\n"
                "⭐ +5 XP\n"
                "🪙 +2 T-Coins"
            ),
            "finished": True
        }

    # =========================================================
    # RIDDLES
    # =========================================================

    def start_riddle(self, user_id):
        riddle = random.choice(
            self.riddles
        )

        self.active_games[user_id] = {
            "type": "riddle",
            "riddle": riddle
        }

        return (
            "🧩 ЗАГАДКА\n\n"
            f"{riddle['question']}\n\n"
            "Напиши ответ."
        )

    def check_riddle(self, user_id, answer):
        game = self.active_games.get(user_id)

        if not game or game["type"] != "riddle":
            return None

        riddle = game["riddle"]

        answer = answer.strip().lower()

        correct = answer in [
            item.lower()
            for item in riddle["answers"]
        ]

        self.active_games.pop(
            user_id,
            None
        )

        if correct:
            reward = riddle["reward"]

            self.finish_game(
                user_id,
                True,
                xp=reward,
                coins=reward
            )

            return {
                "message": (
                    "🎉 Верно!\n\n"
                    f"⭐ +{reward} XP\n"
                    f"🪙 +{reward} T-Coins"
                ),
                "finished": True
            }

        self.finish_game(
            user_id,
            False,
            xp=5,
            coins=2
        )

        return {
            "message": (
                "❌ Не угадал.\n\n"
                f"Ответ: {riddle['answers'][0]}\n\n"
                "⭐ +5 XP\n"
                "🪙 +2 T-Coins"
            ),
            "finished": True
        }

    # =========================================================
    # REACTION
    # =========================================================

    def start_reaction(self, user_id):
        self.active_games[user_id] = {
            "type": "reaction",
            "target": "⚡"
        }

        return (
            "⚡ REACTION\n\n"
            "Готов?\n\n"
            "Как только увидишь ⚡ — "
            "отправь его!"
        )

    def check_reaction(self, user_id, answer):
        game = self.active_games.get(user_id)

        if not game or game["type"] != "reaction":
            return None

        self.active_games.pop(
            user_id,
            None
        )

        if answer.strip() == "⚡":
            self.finish_game(
                user_id,
                True,
                xp=15,
                coins=15
            )

            return {
                "message": (
                    "⚡ Отличная реакция!\n\n"
                    "⭐ +15 XP\n"
                    "🪙 +15 T-Coins"
                ),
                "finished": True
            }

        self.finish_game(
            user_id,
            False,
            xp=3,
            coins=1
        )

        return {
            "message": (
                "❌ Неверный ответ.\n\n"
                "⭐ +3 XP\n"
                "🪙 +1 T-Coin"
            ),
            "finished": True
        }

    # =========================================================
    # GAME STATE
    # =========================================================

    def get_active_game(self, user_id):
        return self.active_games.get(
            user_id
        )

    def cancel_game(self, user_id):
        self.active_games.pop(
            user_id,
            None
        )

    # =========================================================
    # REWARDS
    # =========================================================

    def finish_game(
        self,
        user_id,
        won,
        xp,
        coins
    ):
        self.database.increment_games(
            user_id,
            won=won
        )

        self.database.add_xp(
            user_id,
            xp
        )

        self.database.add_coins(
            user_id,
            coins
        )

        # Первое сыгранное событие
        self.database.unlock_achievement(
            user_id,
            "First Game"
        )

        # Достижение миллионера
        user = self.database.get_user(
            user_id
        )

        if user and user["coins"] >= 1_000_000:
            self.database.unlock_achievement(
                user_id,
                "Millionaire"
            )
