from django.contrib import admin
from .models import TrackedItem

@admin.register(TrackedItem)
class TrackedItemAdmin(admin.ModelAdmin):
    list_display = ("name", "target_price", "last_min_price", "last_avg_price", "created_at")
    search_fields = ("name",)