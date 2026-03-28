import os
import django
import time
from django.utils import timezone

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warframe_market_tracker.settings")
django.setup()

from tracker.models import TrackedItem, Notification
from tracker.services.market_api import get_item_prices


CHECK_INTERVAL = 120  # 30 секунд
NOTIFY_COOLDOWN = 3600  # 1 час


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

        # обновляем цены
        item.last_min_price = min_price
        item.last_avg_price = avg_price
        item.save(update_fields=["last_min_price", "last_avg_price"])

        if should_notify(item, min_price):

            Notification.objects.create(
                user=item.user,
                text=(
                    f"{item.name}: цена достигла {min_price} plat "
                    f"(цель: {item.target_price})"
                ),
                tracked_item=item
            )

            item.last_notified_at = timezone.now()
            item.save(update_fields=["last_notified_at"])

            print(f"[NOTIFY] {item.name} -> {min_price}")

    except Exception as e:
        print(f"[ERROR] {item.name}: {e}")


def run_watcher():

    print("Price watcher started")

    while True:
        items = TrackedItem.objects.all()

        print(f"[INFO] checking {items.count()} items")

        for item in items:
            process_item(item)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_watcher()