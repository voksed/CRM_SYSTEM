from functools import wraps

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .models import User


def is_owner(user) -> bool:
    return user.role == User.Role.OWNER


def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_owner(request.user):
            raise PermissionDenied("Доступно только владельцу организации.")
        return view_func(request, *args, **kwargs)

    return wrapper


def scope_to_owner_field(queryset, user, field="responsible"):
    """Владелец видит все записи организации, менеджер — только свои."""
    if is_owner(user):
        return queryset
    return queryset.filter(**{field: user})


def scope_claimable(queryset, user, field="responsible"):
    """Как scope_to_owner_field, но менеджер дополнительно видит записи без
    ответственного — их можно забрать в работу самому, не дожидаясь владельца."""
    if is_owner(user):
        return queryset
    return queryset.filter(Q(**{field: user}) | Q(**{f"{field}__isnull": True}))
