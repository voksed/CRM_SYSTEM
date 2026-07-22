from contacts.models import Contact

from .adapters import ChannelNotConnected, get_channel
from .models import Activity


def send_message(organization, contact, channel_code, text, user=None):
    """Отправляет сообщение через выбранный канал и логирует это в единой ленте
    коммуникаций контакта — вне зависимости от результата отправки."""
    channel = get_channel(channel_code, organization)
    try:
        channel.send(contact, text)
        status_note = ""
    except ChannelNotConnected as exc:
        status_note = f"\n\n[не отправлено: {exc}]"

    return Activity.objects.create(
        organization=organization,
        contact=contact,
        type=Activity.Type.MESSAGE,
        channel=channel_code,
        direction=Activity.Direction.OUT,
        text=text + status_note,
        created_by=user,
    )


def receive_telegram_message(organization, chat_id: str, text: str, sender_name: str = ""):
    """Обрабатывает входящее сообщение Telegram-бота. Если чат ещё не привязан
    ни к одному контакту — это и есть автоматический захват лида из соцсетей."""
    contact = Contact.objects.filter(
        organization=organization, telegram_chat_id=chat_id
    ).first()

    if contact is None:
        contact = Contact.objects.create(
            organization=organization,
            full_name=sender_name or f"Telegram {chat_id}",
            source=Contact.Source.SOCIAL,
            status=Contact.Status.NEW,
            telegram_chat_id=chat_id,
        )

    Activity.objects.create(
        organization=organization,
        contact=contact,
        type=Activity.Type.MESSAGE,
        channel=Activity.Channel.TELEGRAM,
        direction=Activity.Direction.IN,
        text=text,
    )
    return contact
