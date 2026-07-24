from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    unread_count = notifications.filter(is_read=False).count()
    context = {
        "notifications": notifications[:100],
        "unread_count": unread_count,
    }
    return render(request, "notifications/list.html", context)


@login_required
def notification_open(request, notification_id):
    """Отмечает уведомление прочитанным и ведёт к связанному объекту."""
    notification = get_object_or_404(
        Notification, pk=notification_id, recipient=request.user
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect(notification.url or "notification_list")


@login_required
@require_POST
def notification_read_all(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect("notification_list")
