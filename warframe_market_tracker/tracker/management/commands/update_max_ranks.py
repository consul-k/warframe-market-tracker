# tracker/management/commands/update_max_ranks.py
import time
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import MarketItem

BASE_ITEM_URL = "https://api.warframe.market/v1/items/{url_name}"


class Command(BaseCommand):
    help = "Обновляет поле max_rank у MarketItem, запрашивая подробности предмета из Warframe.Market"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0,
                            help="Максимум обработать записей за запуск (0 — без лимита)")
        parser.add_argument("--sleep", type=float, default=0.12,
                            help="Задержка между запросами к API в секундах (по умолчанию 0.12)")

    def handle(self, *args, **options):
        limit = options["limit"]
        sleep = options["sleep"]

        qs = MarketItem.objects.filter(max_rank__isnull=True).order_by("id")
        if limit and limit > 0:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Нет предметов без max_rank — ничего не делать."))
            return

        self.stdout.write(f"Будет обработано {total} предметов (limit={limit}, sleep={sleep}).")

        processed = 0
        updated = 0
        errors = 0

        for mi in qs:
            url_name = mi.item_url_name
            if not url_name:
                self.stdout.write(self.style.WARNING(f"Пропуск (нет item_url_name): id={mi.id}"))
                continue

            try:
                resp = requests.get(BASE_ITEM_URL.format(url_name=url_name), timeout=10)
                if resp.status_code != 200:
                    self.stdout.write(self.style.WARNING(f"{mi.item_url_name}: status {resp.status_code}"))
                    errors += 1
                else:
                    data = resp.json()
                    # Попробуем взять mod_max_rank из валидного места (в API структура может отличаться)
                    # Пробуем несколько вариантов доступа к данным
                    payload = data.get("payload", {})
                    # вариант: payload.item.items_in_set -> список частей
                    max_rank = None
                    item_block = payload.get("item", {}) or {}
                    items_in_set = item_block.get("items_in_set") or []
                    if items_in_set:
                        for part in items_in_set:
                            # некоторые части могут не содержать url_name, проверяем
                            if part.get("url_name") == url_name:
                                max_rank = part.get("mod_max_rank")
                                break
                    # если не нашли — попытка искать модификатор в других местах
                    if max_rank is None:
                        # иногда API может давать сразу поле mod_max_rank в payload
                        max_rank = payload.get("mod_max_rank")

                    # Сохраняем (даже если max_rank == None, можно оставить как null)
                    if max_rank is not None:
                        with transaction.atomic():
                            mi.max_rank = max_rank
                            mi.save(update_fields=["max_rank"])
                        updated += 1
                        self.stdout.write(self.style.SUCCESS(f"Updated {url_name} -> max_rank={max_rank}"))
                    else:
                        self.stdout.write(self.style.NOTICE(f"No rank for {url_name}"))
                processed += 1
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"Error for {url_name}: {e}"))

            # Небольшая пауза, чтобы не спамить API (настраивается опцией --sleep)
            time.sleep(sleep)

        self.stdout.write(self.style.SUCCESS(
            f"Готово: processed={processed}, updated={updated}, errors={errors}"
        ))