from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Организация", {"fields": ("organization", "role", "phone")}),
    )
    list_display = ("username", "email", "role", "organization", "is_staff")
    list_filter = UserAdmin.list_filter + ("role", "organization")
