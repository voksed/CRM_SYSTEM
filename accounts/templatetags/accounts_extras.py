from django import template

register = template.Library()


@register.filter
def initials(user):
    name = (getattr(user, "get_full_name", lambda: "")() or getattr(user, "username", "") or str(user)).strip()
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "?"
