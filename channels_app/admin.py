from django.contrib import admin

from .models import Activity, TelegramAccount


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("organization", "bot_username", "is_active", "created_at")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("contact", "deal", "type", "channel", "direction", "created_at")
    list_filter = ("organization", "type", "channel", "direction")
