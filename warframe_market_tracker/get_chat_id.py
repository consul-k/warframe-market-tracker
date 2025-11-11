# get_chat_id.py
import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN") or "ВАШ_TOKEN_СЮДА"

def get_updates():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    r = requests.get(url)
    print(r.json())

if __name__ == "__main__":
    get_updates()
