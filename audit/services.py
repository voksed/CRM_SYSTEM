from .models import AuditLog


def get_client_ip(request):
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(
    actor,
    action,
    obj=None,
    organization=None,
    model_name="",
    object_repr="",
    ip_address=None,
    actor_username="",
):
    """Пишет запись в журнал событий. actor может быть None (например,
    для неудачной попытки входа с несуществующим логином)."""
    resolved_organization = organization or getattr(actor, "organization", None)
    return AuditLog.objects.create(
        organization=resolved_organization,
        actor=actor if actor and getattr(actor, "pk", None) else None,
        actor_username=actor_username or getattr(actor, "username", "") or "",
        action=action,
        model_name=model_name or (obj.__class__.__name__ if obj is not None else ""),
        object_repr=object_repr or (str(obj) if obj is not None else ""),
        ip_address=ip_address,
    )
