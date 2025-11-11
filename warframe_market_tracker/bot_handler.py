import os
import django
import requests

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warframe_market_tracker.settings")
django.setup()

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

LAST_UPDATE_FILE = "last_update_id.txt"


def get_last_update_id():
    if not os.path.exists(LAST_UPDATE_FILE):
        return None
    with open(LAST_UPDATE_FILE, "r") as f:
        return int(f.read().strip())


def set_last_update_id(update_id):
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(str(update_id))


def send_message(chat_id, text):
    """Отправка простого текстового сообщения"""
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(API_URL + "sendMessage", json=data)


def handle_updates():
    """Минимальная обработка команд — только /start"""
    last_update_id = get_last_update_id()
    params = {"offset": last_update_id + 1} if last_update_id else {}

    resp = requests.get(API_URL + "getUpdates", params=params)
    data = resp.json()

    if not data.get("ok"):
        print("Ошибка при запросе getUpdates")
        return

    for update in data["result"]:
        update_id = update["update_id"]
        message = update.get("message")
        if not message:
            continue

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text == "/start":
            send_message(
                chat_id,
                "👋 Привет! Это Warframe Market Tracker Bot.\n"
                "🔔 Я уведомлю тебя, когда предмет достигнет целевой цены."
            )
        else:
            send_message(chat_id, "ℹ️ Сейчас бот работает только для уведомлений.")

        set_last_update_id(update_id)


if __name__ == "__main__":
    handle_updates()
