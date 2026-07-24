from contacts.models import Contact

from .adapters import ChannelNotConnected, get_channel
from .models import Activity


def send_message(organization, contact, channel_code, text, user=None):
    """Отправляет сообщение через выбранный канал и логирует это в единой ленте
    коммуникаций контакта — вне зависимости от результата отправки."""
    channel = get_channel(channel_code, organization)
    failed = False
    error = ""
    try:
        channel.send(contact, text)
    except ChannelNotConnected as exc:
        failed = True
        error = str(exc)[:500]

    return Activity.objects.create(
        organization=organization,
        contact=contact,
        type=Activity.Type.MESSAGE,
        channel=channel_code,
        direction=Activity.Direction.OUT,
        text=text,
        delivery_failed=failed,
        delivery_error=error,
        created_by=user,
    )


def receive_telegram_message(account, chat_id: str, text: str, sender_name: str = ""):
    """Обрабатывает входящее сообщение конкретного Telegram-бота. Если чат ещё
    не привязан ни к одному контакту — это автоматический захват лида.

    Возвращает кортеж (activity, created), где created=True, если контакт был
    создан этим сообщением (нужно, чтобы запустить анкету новому клиенту)."""
    organization = account.organization
    contact = Contact.objects.filter(
        organization=organization, telegram_chat_id=chat_id
    ).first()

    created = False
    if contact is None:
        contact = Contact.objects.create(
            organization=organization,
            full_name=sender_name or f"Telegram {chat_id}",
            source=Contact.Source.SOCIAL,
            status=Contact.Status.NEW,
            telegram_chat_id=chat_id,
            telegram_account=account,
        )
        created = True
    elif contact.telegram_account_id != account.id:
        contact.telegram_account = account
        contact.save(update_fields=["telegram_account"])

    activity = Activity.objects.create(
        organization=organization,
        contact=contact,
        type=Activity.Type.MESSAGE,
        channel=Activity.Channel.TELEGRAM,
        direction=Activity.Direction.IN,
        text=text,
    )
    return activity, created
