from django.db import models
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


class MarketItem(models.Model):
    item_name = models.CharField(max_length=255, db_index=True)
    item_url_name = models.CharField(max_length=255, unique=True)
    max_rank = models.PositiveSmallIntegerField(null=True, blank=True)

    min_price = models.FloatField(null=True, blank=True)
    avg_price = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.item_name

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    text = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    tracked_item = models.ForeignKey(
        TrackedItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user} | {self.text[:50]}"