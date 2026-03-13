from django.contrib import admin
from .models import TrackedItem, TelegramAuthToken, TelegramProfile

@admin.register(TrackedItem)
class TrackedItemAdmin(admin.ModelAdmin):
    list_display = ("name", "target_price", "last_min_price", "last_avg_price", "created_at")
    search_fields = ("name",)

@admin.register(TelegramAuthToken)
class TelegramAuthTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "is_used", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("token",)
    readonly_fields = ("token", "created_at")

@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("telegram_id",)
    search_fields = ("telegram_id",)