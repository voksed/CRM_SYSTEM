from django.conf import settings
from django.db import models

from accounts.models import Organization
from contacts.models import Contact
from deals.models import Deal


class TelegramAccount(models.Model):
    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="telegram_account"
    )
    bot_token = models.CharField(max_length=200)
    bot_username = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_update_id = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bot_username or f"Telegram-бот организации {self.organization}"


class Activity(models.Model):
    class Type(models.TextChoices):
        CALL = "call", "Звонок"
        MESSAGE = "message", "Сообщение"
        EMAIL = "email", "Email"
        NOTE = "note", "Заметка"
        SYSTEM = "system", "Системное событие"

    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"
        VK = "vk", "VK"
        PHONE = "phone", "Телефон"
        EMAIL = "email", "Email"
        MANUAL = "manual", "Вручную"

    class Direction(models.TextChoices):
        IN = "in", "Входящее"
        OUT = "out", "Исходящее"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="activities"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, null=True, blank=True, related_name="activities"
    )
    deal = models.ForeignKey(
        Deal, on_delete=models.CASCADE, null=True, blank=True, related_name="activities"
    )
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name="Тип")
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.MANUAL, verbose_name="Канал"
    )
    direction = models.CharField(
        max_length=10, choices=Direction.choices, blank=True, verbose_name="Направление"
    )
    text = models.TextField(blank=True, verbose_name="Текст")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self):
        return f"{self.get_type_display()} ({self.get_channel_display()}) — {self.contact}"
