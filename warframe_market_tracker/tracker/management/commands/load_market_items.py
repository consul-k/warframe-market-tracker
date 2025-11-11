import requests
from django.core.management.base import BaseCommand
from tracker.models import MarketItem
import time

API_URL = "https://api.warframe.market/v1/items"
ITEM_DETAIL_URL = "https://api.warframe.market/v1/items/{url_name}"

class Command(BaseCommand):
    help = "Загружает список предметов из Warframe Market и сохраняет в MarketItem, включая max_rank для модов"

    def handle(self, *args, **options):
        response = requests.get(API_URL)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Ошибка запроса: {response.status_code}"))
            return

        data = response.json()
        items = data.get("payload", {}).get("items", [])

        count_new = 0
        count_with_rank = 0

        for item_data in items:
            url_name = item_data["url_name"]
            name = item_data["item_name"]

            # Получаем детали предмета (чтобы узнать mod_max_rank)
            detail_resp = requests.get(ITEM_DETAIL_URL.format(url_name=url_name))
            if detail_resp.status_code == 200:
                detail_data = detail_resp.json()
                items_in_set = detail_data.get("payload", {}).get("item", {}).get("items_in_set", [])
                max_rank = None
                for part in items_in_set:
                    # если есть ключ mod_max_rank – используем его
                    if part.get("mod_max_rank") is not None:
                        max_rank = part.get("mod_max_rank")
                        break
            else:
                max_rank = None

            MarketItem.objects.update_or_create(
                item_url_name=url_name,
                defaults={
                    "item_name": name,
                    "max_rank": max_rank
                }
            )

            if max_rank is not None:
                count_with_rank += 1

            count_new += 1

            # Немного задержки, чтобы не спамить API
            time.sleep(0.1)

        self.stdout.write(self.style.SUCCESS(
            f"Загружено/обновлено {count_new} предметов, с max_rank задан: {count_with_rank}"
        ))