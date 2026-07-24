from django.contrib import admin

from .models import Activity, LeadQuestion, LeadSession, TelegramAccount


class LeadQuestionInline(admin.TabularInline):
    model = LeadQuestion
    extra = 1


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("__str__", "organization", "bot_username", "is_active", "collect_lead", "created_at")
    list_filter = ("is_active", "collect_lead")
    inlines = [LeadQuestionInline]


@admin.register(LeadSession)
class LeadSessionAdmin(admin.ModelAdmin):
    list_display = ("contact", "account", "current_index", "is_completed", "created_at")
    list_filter = ("is_completed",)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("contact", "deal", "type", "channel", "direction", "created_at")
    list_filter = ("organization", "type", "channel", "direction")
