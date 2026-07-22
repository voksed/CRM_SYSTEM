import datetime

from django.utils import timezone

from channels_app.models import Activity
from tasks.models import Task

from .models import AutomationRule


def apply_action(rule: AutomationRule, deal):
    if rule.action == AutomationRule.Action.CREATE_TASK:
        Task.objects.create(
            organization=deal.organization,
            deal=deal,
            contact=deal.contact,
            assigned_to=deal.responsible or deal.organization.owner,
            task_type=rule.task_type or Task.Type.OTHER,
            title=rule.task_title or rule.name,
            due_at=timezone.now() + datetime.timedelta(hours=rule.task_due_in_hours),
            is_auto_generated=True,
        )
    elif rule.action == AutomationRule.Action.MOVE_TO_STAGE and rule.action_target_stage:
        if deal.stage_id != rule.action_target_stage_id:
            deal.stage = rule.action_target_stage
            deal.save()
    elif rule.action == AutomationRule.Action.LOG_ACTIVITY:
        Activity.objects.create(
            organization=deal.organization,
            deal=deal,
            contact=deal.contact,
            type=Activity.Type.SYSTEM,
            channel=Activity.Channel.MANUAL,
            text=f"Автоматизация «{rule.name}» сработала.",
        )


def run_stage_changed(deal):
    rules = AutomationRule.objects.filter(
        organization=deal.organization,
        trigger=AutomationRule.Trigger.STAGE_CHANGED,
        trigger_stage=deal.stage,
        is_active=True,
    )
    for rule in rules:
        apply_action(rule, deal)


def run_payment_received(payment):
    deal = payment.deal
    rules = AutomationRule.objects.filter(
        organization=deal.organization,
        trigger=AutomationRule.Trigger.PAYMENT_RECEIVED,
        is_active=True,
    )
    for rule in rules:
        apply_action(rule, deal)


def run_stale_deal_check():
    """Находит сделки без активности дольше N дней (по правилам с триггером
    no_activity) и применяет действие. Предназначено для periodic-запуска
    (management command / cron)."""
    from deals.models import Deal

    rules = AutomationRule.objects.filter(
        trigger=AutomationRule.Trigger.NO_ACTIVITY, is_active=True
    )
    triggered = 0
    for rule in rules:
        if not rule.no_activity_days:
            continue
        threshold = timezone.now() - datetime.timedelta(days=rule.no_activity_days)
        stale_deals = Deal.objects.filter(
            organization=rule.organization, status=Deal.Status.OPEN
        ).exclude(activities__created_at__gte=threshold)
        for deal in stale_deals:
            apply_action(rule, deal)
            triggered += 1
    return triggered
