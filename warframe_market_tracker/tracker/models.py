import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

class TrackedItem(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="tracked_items")
    name = models.CharField("Название предмета", max_length=200)
    item_url_name = models.CharField("URL name предмета", max_length=200)
    target_price = models.FloatField("Целевая цена", null=True, blank=True)
    last_min_price = models.FloatField("Последняя минимальная цена", null=True, blank=True)
    last_avg_price = models.FloatField("Последняя средняя цена", null=True, blank=True)
    last_notified_at = models.DateTimeField("Последнее уведомление", null=True, blank=True)
    min_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    max_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "item_url_name")

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
    
def telegram_token_expiry():
    return timezone.now() + timedelta(minutes=5)

class TelegramProfile(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="telegram_profile"
    )
    
class TelegramAuthToken(models.Model):
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    telegram_profile = models.ForeignKey(
        "TelegramProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Заполняется после подтверждения через Telegram"
    )

    is_used = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField(default=telegram_token_expiry)

    def is_valid(self):
        return (
            not self.is_used
            and timezone.now() < self.expires_at
        )

    def __str__(self):
        return f"AuthToken {self.token}"
    
    class Meta:
        indexes = [
        models.Index(fields=["token"]),]
