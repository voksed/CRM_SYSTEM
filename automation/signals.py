from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from billing.models import Payment
from deals.models import Deal

from .engine import run_payment_received, run_stage_changed


@receiver(pre_save, sender=Deal)
def _capture_old_stage(sender, instance, **kwargs):
    if instance.pk:
        instance._old_stage_id = (
            Deal.objects.filter(pk=instance.pk).values_list("stage_id", flat=True).first()
        )
    else:
        instance._old_stage_id = None


@receiver(post_save, sender=Deal)
def _deal_stage_changed(sender, instance, created, **kwargs):
    old_stage_id = getattr(instance, "_old_stage_id", None)
    if created or old_stage_id != instance.stage_id:
        run_stage_changed(instance)


@receiver(post_save, sender=Payment)
def _payment_received(sender, instance, created, **kwargs):
    if created:
        run_payment_received(instance)
