from django.conf import settings
from django.db import models

from accounts.models import Organization


class Notification(models.Model):
    """Персональное уведомление сотрудника о новой задаче, изменении сделки
    или другом важном событии в CRM."""

    class Kind(models.TextChoices):
        TASK = "task", "Задача"
        DEAL = "deal", "Сделка"
        CONTACT = "contact", "Контакт"
        SYSTEM = "system", "Система"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="notifications"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Получатель",
    )
    kind = models.CharField(
        max_length=20, choices=Kind.choices, default=Kind.SYSTEM, verbose_name="Тип"
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    text = models.TextField(blank=True, verbose_name="Текст")
    url = models.CharField(max_length=500, blank=True, verbose_name="Ссылка")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} → {self.recipient}"
