from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def money(value):
    """Форматирует сумму с пробелом-разделителем разрядов: 1 000 000.
    Целые суммы — без копеек, дробные — с двумя знаками через запятую."""
    try:
        amount = Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        return value
    if amount == amount.to_integral_value():
        return f"{int(amount):,}".replace(",", " ")
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return formatted


@register.filter
def initials(user):
    name = (getattr(user, "get_full_name", lambda: "")() or getattr(user, "username", "") or str(user)).strip()
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "?"
