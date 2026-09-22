import os
import json
import urllib.request


class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")

        if not self.token:
            raise RuntimeError("TELEGRAM_TOKEN не установлен")

        self.api_url = (
            f"https://api.telegram.org/bot{self.token}"
        )

    def request(self, method, data=None):
        url = f"{self.api_url}/{method}"

        payload = json.dumps(data or {}).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_me(self):
        return self.request("getMe")
