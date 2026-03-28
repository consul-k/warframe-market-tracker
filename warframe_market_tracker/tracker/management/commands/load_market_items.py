import requests
from django.core.management.base import BaseCommand
from tracker.models import MarketItem


API_URL = "https://api.warframe.market/v2/items"

class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.get(API_URL)

        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Ошибка: {response.status_code}"))
            return

        data = response.json()
        items = data.get("data", [])

        count = 0

        for item in items:
            url_name = item.get("slug")
            name = item.get("i18n", {}).get("en", {}).get("name")

            max_rank = item.get("maxRank")  # сразу бонусом берем

            if not url_name or not name:
                continue

            MarketItem.objects.update_or_create(
                item_url_name=url_name,
                defaults={
                    "item_name": name,
                    "max_rank": max_rank
                }
            )

            count += 1

        self.stdout.write(self.style.SUCCESS(f"Загружено {count} предметов"))
