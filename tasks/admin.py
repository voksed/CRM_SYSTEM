from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "task_type", "assigned_to", "due_at", "is_done", "is_auto_generated")
    list_filter = ("organization", "task_type", "is_done", "is_auto_generated")
