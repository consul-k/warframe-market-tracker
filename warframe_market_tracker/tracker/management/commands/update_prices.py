from django.core.management.base import BaseCommand
from django.utils import timezone
from tracker.models import TrackedItem
from tracker.services.market_api import get_item_prices
from tracker.telegram_utils import send_telegram_message


class Command(BaseCommand):
    help = "Обновляет минимальные и средние цены предметов из Warframe Market и отправляет уведомления при достижении целевой цены"

    def handle(self, *args, **kwargs):
        items = TrackedItem.objects.all()
        if not items.exists():
            self.stdout.write("Нет предметов для обновления.")
            return

        for item in items:
            if not item.item_url_name:
                self.stdout.write(f"⏩ Пропуск: {item.name} (нет item_url_name)")
                continue

            try:
                # 1️⃣ Определяем ранг для модов (если есть)
                rank = item.max_rank if item.max_rank is not None else item.min_rank
                min_p, avg_p = get_item_prices(item.item_url_name, rank)

                if min_p is None and avg_p is None:
                    self.stdout.write(f"⚠️ Не удалось получить цены для {item.name} (rank={rank})")
                    continue

                # 2️⃣ Обновляем базу
                item.last_min_price = min_p
                item.last_avg_price = avg_p

                # 3️⃣ Проверяем условие уведомления
                if item.target_price:
                    # Обычно мы уведомляем, если цена стала ≤ целевой
                    price_to_check = min_p or avg_p
                    if price_to_check <= item.target_price:
                        send_window_hours = 6
                        should_send = (
                            not item.last_notified_at or
                            (timezone.now() - item.last_notified_at).total_seconds() > send_window_hours * 3600
                        )

                        if should_send and item.chat_id:
                            message = (
                                f"🎯 <b>{item.name}</b> достиг целевой цены!\n\n"
                                f"💰 Мин: <b>{min_p}</b> платина\n"
                                f"🎯 Цель: <b>{item.target_price}</b>\n"
                                f"📈 Средняя (48ч): {avg_p}\n\n"
                                f"🔗 https://warframe.market/items/{item.item_url_name}"
                            )
                            send_telegram_message(int(item.chat_id), message)
                            item.last_notified_at = timezone.now()
                            self.stdout.write(f"✅ Уведомление отправлено: {item.name}")
                        elif not item.chat_id:
                            self.stdout.write(f"⚠️ Нет chat_id для {item.name}, уведомление пропущено.")

                # 4️⃣ Сохраняем
                item.save()
                self.stdout.write(f"🔄 Обновлено: {item.name} (rank={rank}) → min={min_p}, avg={avg_p}")

            except Exception as e:
                self.stderr.write(f"❌ Ошибка при обновлении {item.name}: {e}")

        self.stdout.write("✅ Завершено обновление всех цен.")