from django.conf import settings
from django.db import models

from accounts.models import Organization
from contacts.models import Contact
from deals.models import Deal


class Task(models.Model):
    class Type(models.TextChoices):
        CALL = "call", "Позвонить"
        MEETING = "meeting", "Встреча"
        INVOICE = "invoice", "Выставить счёт"
        FOLLOW_UP = "follow_up", "Напомнить о себе"
        OTHER = "other", "Другое"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="tasks"
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Контакт",
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Сделка",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Исполнитель",
    )
    task_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.OTHER, verbose_name="Тип задачи"
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    due_at = models.DateTimeField(verbose_name="Срок выполнения")
    is_done = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_at = models.DateTimeField(null=True, blank=True)
    is_auto_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at"]

    def __str__(self):
        return self.title
