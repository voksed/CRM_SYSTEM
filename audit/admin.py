from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_username", "action", "model_name", "object_repr", "ip_address")
    list_filter = ("organization", "action", "model_name")
    search_fields = ("actor_username", "object_repr", "ip_address")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False
