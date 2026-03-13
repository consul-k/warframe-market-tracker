import os
import django
import requests
import time
from django.db import transaction
from django.utils import timezone

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warframe_market_tracker.settings")
django.setup()

from django.contrib.auth.models import User
from tracker.models import TelegramAuthToken, TelegramProfile

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}/"
LAST_UPDATE_FILE = "last_update_id.txt"


def get_last_update_id():
    if not os.path.exists(LAST_UPDATE_FILE):
        return None
    with open(LAST_UPDATE_FILE, "r") as f:
        value = f.read().strip()
        return int(value) if value else None


def set_last_update_id(update_id):
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(str(update_id))


def send_message(chat_id, text):
    requests.post(
        API_URL + "sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )


def handle_start(chat_id: int, text: str, message: dict):
    parts = text.split(maxsplit=1)

    if len(parts) == 1:
        send_message(
            chat_id,
            "👋 Привет!\n"
            "Чтобы привязать Telegram, перейди на сайт и нажми «Привязать Telegram»."
        )
        return

    token_value = parts[1].strip()

    with transaction.atomic():
        try:
            auth_token = TelegramAuthToken.objects.select_for_update().get(
                token=token_value
            )
        except TelegramAuthToken.DoesNotExist:
            send_message(chat_id, "❌ Токен недействителен.")
            return

        if not auth_token.is_valid():
            send_message(chat_id, "⏳ Токен истёк или уже использован.")
            return

        user_data = message.get("from", {})

        profile, _ = TelegramProfile.objects.get_or_create(
            telegram_id=chat_id,
            defaults={
                "telegram_username": user_data.get("username", "") or "",
                "first_name": user_data.get("first_name", "") or "",
            }
        )

        # Создание User безопасным способом
        if not profile.user:
            username = f"tg_{chat_id}"

            user = User.objects.create_user(
                username=username,
            )

            user.set_unusable_password()
            user.save()
            
            profile.user = user
            profile.save(update_fields=["user"])

        auth_token.telegram_profile = profile
        auth_token.is_used = True
        auth_token.save(update_fields=["telegram_profile", "is_used"])

    send_message(chat_id, "✅ Telegram успешно привязан.")


def handle_updates():
    last_update_id = get_last_update_id()
    params = {"offset": last_update_id + 1} if last_update_id else {}

    try:
        resp = requests.get(API_URL + "getUpdates", params=params, timeout=30)
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] Telegram request failed: {e}")
        return

    if not data.get("ok"):
        return

    for update in data["result"]:
        update_id = update["update_id"]
        message = update.get("message")

        if not message:
            set_last_update_id(update_id)
            continue

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text.startswith("/start"):
            handle_start(chat_id, text, message)
        else:
            send_message(chat_id, "ℹ️ Сейчас бот работает только для уведомлений.")

        set_last_update_id(update_id)

if __name__ == "__main__":
    while True:
        handle_updates()
        time.sleep(2)