from django.contrib import admin

from .models import Contact, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "color")
    list_filter = ("organization",)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("full_name", "source", "status", "responsible", "organization", "created_at")
    list_filter = ("organization", "source", "status", "tags")
    search_fields = ("full_name", "phone", "email")
