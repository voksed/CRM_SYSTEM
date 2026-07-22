from decimal import Decimal

from django.db.models import Sum

from deals.models import Deal

from .models import Payment


def calculate_balance(deal: Deal) -> Decimal:
    """Сколько осталось получить по сделке: сумма сделки минус все оплаты.
    Положительное число — остаток долга, отрицательное — переплата."""
    paid = Payment.objects.filter(deal=deal).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0")
    return deal.amount - paid
