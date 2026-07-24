from .models import Notification


def notifications(request):
    """Отдаёт в каждый шаблон счётчик непрочитанных и последние уведомления —
    для колокольчика/бейджа в боковом меню."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}

    qs = Notification.objects.filter(recipient=user)
    return {
        "unread_notifications_count": qs.filter(is_read=False).count(),
        "recent_notifications": list(qs[:8]),
    }
