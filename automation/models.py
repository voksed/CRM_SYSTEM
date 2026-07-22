from django.db import models

from accounts.models import Organization
from deals.models import Stage
from tasks.models import Task


class AutomationRule(models.Model):
    class Trigger(models.TextChoices):
        STAGE_CHANGED = "stage_changed", "Сделка перешла на этап"
        PAYMENT_RECEIVED = "payment_received", "Получена оплата"
        NO_ACTIVITY = "no_activity", "Нет активности по сделке N дней"

    class Action(models.TextChoices):
        CREATE_TASK = "create_task", "Создать задачу"
        MOVE_TO_STAGE = "move_to_stage", "Переместить сделку на этап"
        LOG_ACTIVITY = "log_activity", "Записать системное событие"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="automation_rules"
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    trigger = models.CharField(max_length=30, choices=Trigger.choices, verbose_name="Триггер")
    trigger_stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Этап-триггер",
        help_text="Для триггера «Сделка перешла на этап»",
    )
    no_activity_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Дней без активности",
        help_text="Для триггера «Нет активности N дней»",
    )

    action = models.CharField(max_length=30, choices=Action.choices, verbose_name="Действие")
    action_target_stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Целевой этап",
        help_text="Для действия «Переместить сделку на этап»",
    )
    task_type = models.CharField(
        max_length=20,
        choices=Task.Type.choices,
        blank=True,
        verbose_name="Тип задачи",
        help_text="Для действия «Создать задачу»",
    )
    task_title = models.CharField(max_length=255, blank=True, verbose_name="Текст задачи")
    task_due_in_hours = models.PositiveIntegerField(
        default=24, verbose_name="Срок задачи, часов"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
