from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import Organization
from contacts.models import Contact


class Pipeline(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="pipelines"
    )
    name = models.CharField(max_length=100, default="Продажи", verbose_name="Название")

    def __str__(self):
        return self.name


class Stage(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name="stages")
    name = models.CharField(max_length=100, verbose_name="Название")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_won = models.BooleanField(default=False, verbose_name="Успешный этап")
    is_lost = models.BooleanField(default=False, verbose_name="Отказной этап")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Deal(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "В работе"
        WON = "won", "Успешно"
        LOST = "lost", "Отказ"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="deals"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="deals", verbose_name="Контакт"
    )
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name="deals")
    stage = models.ForeignKey(
        Stage, on_delete=models.CASCADE, related_name="deals", verbose_name="Этап"
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма"
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        verbose_name="Ответственный",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.stage.is_won:
            self.status = self.Status.WON
            self.closed_at = self.closed_at or timezone.now()
        elif self.stage.is_lost:
            self.status = self.Status.LOST
            self.closed_at = self.closed_at or timezone.now()
        else:
            self.status = self.Status.OPEN
            self.closed_at = None
        super().save(*args, **kwargs)
