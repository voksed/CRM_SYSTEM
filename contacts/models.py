from django.conf import settings
from django.db import models

from accounts.models import Organization


class Tag(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="tags"
    )
    name = models.CharField(max_length=50, verbose_name="Название")
    color = models.CharField(
        max_length=7, default="#2563eb", verbose_name="Цвет", help_text="HEX-цвет метки"
    )

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class Contact(models.Model):
    class Source(models.TextChoices):
        WEBSITE = "website", "Сайт"
        ADS = "ads", "Реклама"
        SOCIAL = "social", "Соцсети/мессенджеры"
        REFERRAL = "referral", "Рекомендация"
        COLD_CALL = "cold_call", "Холодный звонок"
        OTHER = "other", "Другое"

    class Status(models.TextChoices):
        NEW = "new", "Новый лид"
        IN_PROGRESS = "in_progress", "В работе"
        CLIENT = "client", "Клиент"
        LOST = "lost", "Потерян"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="contacts"
    )
    full_name = models.CharField(max_length=255, verbose_name="Полное имя")
    phone = models.CharField(max_length=32, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.OTHER, verbose_name="Источник"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Статус"
    )
    tags = models.ManyToManyField(Tag, related_name="contacts", blank=True, verbose_name="Теги")
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
        verbose_name="Ответственный",
    )
    telegram_chat_id = models.CharField(
        max_length=64, blank=True, verbose_name="Telegram chat ID"
    )
    notes = models.TextField(blank=True, verbose_name="Заметки")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name
