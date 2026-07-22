from django.contrib import admin

from .models import Deal, Pipeline, Stage


class StageInline(admin.TabularInline):
    model = Stage
    extra = 1


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ("name", "organization")
    list_filter = ("organization",)
    inlines = [StageInline]


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("title", "contact", "pipeline", "stage", "amount", "status", "responsible")
    list_filter = ("organization", "pipeline", "stage", "status")
    search_fields = ("title",)
