from .models import Notification


def notify(recipient, title, *, text="", url="", kind=Notification.Kind.SYSTEM, actor=None):
    """Создаёт уведомление для сотрудника.

    Не отправляет уведомление самому себе (когда actor совпадает с получателем)
    и молча игнорирует случай, когда получатель не задан (например, у сделки
    ещё нет ответственного)."""
    if recipient is None:
        return None
    if actor is not None and actor.pk == recipient.pk:
        return None

    return Notification.objects.create(
        organization=recipient.organization,
        recipient=recipient,
        kind=kind,
        title=title,
        text=text,
        url=url,
    )
