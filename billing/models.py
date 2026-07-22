import uuid

from django.db import models

from accounts.models import Organization
from deals.models import Deal


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Не оплачен"
        PAID = "paid", "Оплачен"
        OVERDUE = "overdue", "Просрочен"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invoices"
    )
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="invoices")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    public_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Счёт по сделке «{self.deal}» на {self.amount}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Наличные"
        CARD = "card", "Карта/перевод"
        OTHER = "other", "Другое"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="payments"
    )
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="payments")
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    method = models.CharField(
        max_length=20, choices=Method.choices, default=Method.CASH, verbose_name="Способ оплаты"
    )
    paid_at = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий")

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self):
        return f"{self.amount} по сделке «{self.deal}» ({self.get_method_display()})"
