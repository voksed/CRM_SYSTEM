from django.conf import settings
from django.db import models

from accounts.models import Organization


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Создано"
        UPDATED = "updated", "Изменено"
        DELETED = "deleted", "Удалено"
        MOVED = "moved", "Перемещено"
        LOGIN_SUCCESS = "login_success", "Вход выполнен"
        LOGIN_FAILED = "login_failed", "Неудачная попытка входа"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Кто",
    )
    actor_username = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Логин",
        help_text="Фиксируется на момент события — не теряется при удалении аккаунта",
    )
    action = models.CharField(max_length=20, choices=Action.choices, verbose_name="Действие")
    model_name = models.CharField(max_length=50, blank=True, verbose_name="Объект")
    object_repr = models.CharField(max_length=255, blank=True, verbose_name="Описание")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Когда")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Событие журнала"
        verbose_name_plural = "Журнал событий"

    def __str__(self):
        who = self.actor_username or "система"
        return f"{who}: {self.get_action_display()} {self.model_name} «{self.object_repr}»"
