from django.contrib import admin

from .models import AutomationRule


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "trigger", "action", "is_active")
    list_filter = ("organization", "trigger", "action", "is_active")
