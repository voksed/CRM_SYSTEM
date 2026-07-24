"""Трансляция событий чата подключённым браузерам через WebSocket (Channels).

Payload одинаков для входящих (из Telegram) и исходящих (ответ менеджера)
сообщений, поэтому фронтенд рисует их единообразно."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def chat_group_name(contact_id) -> str:
    return f"tg_chat_{contact_id}"


def activity_payload(activity) -> dict:
    return {
        "id": activity.id,
        "direction": activity.direction or "",
        "text": activity.text,
        "created_at": timezone.localtime(activity.created_at).strftime("%d.%m %H:%M"),
        "failed": activity.delivery_failed,
        "error": activity.delivery_error,
    }


async def abroadcast_activity(activity) -> None:
    """Асинхронная трансляция — вызывать из async-контекста (обработчик бота,
    WebSocket-consumer), где событийный цикл совпадает с циклом слоя каналов."""
    if activity is None or activity.contact_id is None:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    await layer.group_send(
        chat_group_name(activity.contact_id),
        {"type": "chat.message", "message": activity_payload(activity)},
    )


def broadcast_activity(activity) -> None:
    """Синхронная обёртка — для sync-контекста (например, HTTP webhook).
    Безопасна при слое каналов с общей шиной (channels_redis)."""
    if activity is None or activity.contact_id is None:
        return
    async_to_sync(abroadcast_activity)(activity)
