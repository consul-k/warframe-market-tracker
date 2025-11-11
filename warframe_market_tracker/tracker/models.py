from django.db import models
from django.utils import timezone

class TrackedItem(models.Model):
    name = models.CharField("Название предмета", max_length=200)
    item_url_name = models.CharField("URL name предмета", max_length=200)
    target_price = models.FloatField("Целевая цена", null=True, blank=True)
    last_min_price = models.FloatField("Последняя минимальная цена", null=True, blank=True)
    last_avg_price = models.FloatField("Последняя средняя цена", null=True, blank=True)
    last_notified_at = models.DateTimeField("Последнее уведомление", null=True, blank=True)
    chat_id = models.CharField("Telegram chat_id", max_length=64, null=True, blank=True)
    min_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    max_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TrackedItemState(models.Model):
    chat_id = models.CharField("Telegram chat_id", max_length=64)
    step = models.CharField("Шаг диалога", max_length=32, default="waiting")
    temp_name = models.CharField("Временное имя предмета", max_length=200, blank=True, null=True)
    temp_target_price = models.FloatField("Временная целевая цена", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

class MarketItem(models.Model):
    item_name = models.CharField(max_length=255, db_index=True)       # Человекочитаемое имя
    item_url_name = models.CharField(max_length=255, unique=True)   # Для API
    max_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.item_name