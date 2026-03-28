from django.contrib import admin
from .models import TrackedItem, MarketItem, Notification

@admin.register(TrackedItem)
class TrackedItemAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "target_price", "last_min_price", "last_avg_price", "created_at")
    search_fields = ("name",)
    list_filter = ("user",)


@admin.register(MarketItem)
class MarketItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "item_url_name", "max_rank", "updated_at")
    search_fields = ("item_name", "item_url_name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("text",)