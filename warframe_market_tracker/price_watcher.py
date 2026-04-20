import os
import django
import time
import logging
import requests
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warframe_market_tracker.settings")
django.setup()

from tracker.models import TrackedItem, Notification
from tracker.services.market_api import get_item_prices


CHECK_INTERVAL = 120
NOTIFY_COOLDOWN = 3600
RATE_LIMIT_SLEEP = 180  # 3 минуты при 429


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def should_notify(item, min_price):
    if item.target_price is None or min_price is None:
        return False

    if min_price < item.target_price:
        return False

    if item.last_notified_at:
        seconds = (timezone.now() - item.last_notified_at).total_seconds()
        if seconds < NOTIFY_COOLDOWN:
            return False

    return True


def process_item_logic(item, min_price, avg_price):
    item.last_min_price = min_price
    item.last_avg_price = avg_price
    item.save(update_fields=["last_min_price", "last_avg_price"])

    if should_notify(item, min_price):
        Notification.objects.create(
            user=item.user,
            text=f"{item.name}: цена достигла {min_price} plat (цель: {item.target_price})",
            tracked_item=item,
        )

        item.last_notified_at = timezone.now()
        item.save(update_fields=["last_notified_at"])

        logging.info(f"[NOTIFY] {item.name} -> {min_price}")


def fetch_prices_with_retry(url_name, rank):
    try:
        return get_item_prices(url_name, rank)

    except ValueError as e:
        # сюда попадёт status != 200
        if "status=429" in str(e):
            logging.warning(f"[RATE LIMIT] {url_name}, sleep {RATE_LIMIT_SLEEP}s")
            time.sleep(RATE_LIMIT_SLEEP)
            return None, None

        logging.error(f"[API ERROR] {url_name}: {e}")
        return None, None

    except requests.RequestException as e:
        logging.error(f"[NETWORK ERROR] {url_name}: {e}")
        return None, None

    except Exception as e:
        logging.exception(f"[UNKNOWN ERROR] {url_name}: {e}")
        return None, None


def run_watcher():
    logging.info("Price watcher started")

    while True:
        try:
            unique_items = (
                TrackedItem.objects
                .values("item_url_name", "max_rank")
                .distinct()
            )

            logging.info(f"[INFO] checking unique market items")

            for entry in unique_items:
                url_name = entry["item_url_name"]
                rank = entry["max_rank"]

                min_price, avg_price = fetch_prices_with_retry(url_name, rank)

                if min_price is None:
                    continue

                related_items = TrackedItem.objects.filter(
                    item_url_name=url_name,
                    max_rank=rank
                )

                for item in related_items:
                    process_item_logic(item, min_price, avg_price)

                time.sleep(1.5)

        except Exception:
            logging.exception("[CRITICAL LOOP ERROR]")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_watcher()