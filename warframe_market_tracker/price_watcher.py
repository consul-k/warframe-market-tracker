import os
import django
import time
import requests
from django.utils import timezone

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warframe_market_tracker.settings")
django.setup()

from tracker.models import TrackedItem
from tracker.services.market_api import get_item_prices


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

CHECK_INTERVAL = 300  # 5 минут
NOTIFY_COOLDOWN = 3600  # 1 час между уведомлениями


def send_telegram(chat_id, text):
    try:
        requests.post(
            TELEGRAM_API,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=10,
        )
    except Exception as e:
        print(f"[ERROR] Telegram send failed: {e}")

def should_notify(item, min_price):

    if item.target_price is None:
        return False

    if min_price is None:
        return False

    # SELL логика
    if min_price < item.target_price:
        return False

    if item.last_notified_at:
        seconds = (timezone.now() - item.last_notified_at).total_seconds()
        if seconds < NOTIFY_COOLDOWN:
            return False

    return True

def process_item(item):
    try:
        rank = item.max_rank if item.max_rank is not None else None

        min_price, avg_price = get_item_prices(item.item_url_name, rank)

        item.last_min_price = min_price
        item.last_avg_price = avg_price
        item.save(update_fields=["last_min_price", "last_avg_price"])

        if should_notify(item, min_price):

            chat_id = item.user.telegram_profile.telegram_id

            text = (
                f"📉 <b>Цена упала!</b>\n\n"
                f"Предмет: <b>{item.name}</b>\n"
                f"Минимальная цена: <b>{min_price} plat</b>\n"
                f"Средняя цена: {avg_price} plat\n"
                f"Целевая цена: {item.target_price} plat\n\n"
                f"https://warframe.market/items/{item.item_url_name}"
            )

            send_telegram(chat_id, text)

            item.last_notified_at = timezone.now()
            item.save(update_fields=["last_notified_at"])

            print(f"[NOTIFY] {item.name} -> {min_price}")

    except Exception as e:
        print(f"[ERROR] {item.name}: {e}")


def run_watcher():

    print("Price watcher started")

    while True:

        items = TrackedItem.objects.select_related(
            "user__telegram_profile"
        ).all()

        print(f"[INFO] checking {items.count()} items")

        for item in items:
            process_item(item)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_watcher()