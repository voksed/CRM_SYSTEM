import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from accounts.permissions import is_owner, scope_claimable
from contacts.models import Contact

from .models import Activity
from .realtime import abroadcast_activity, chat_group_name
from .services import send_message


class TelegramChatConsumer(AsyncWebsocketConsumer):
    """WebSocket-канал переписки с одним контактом. Входящие из Telegram и
    ответы менеджера транслируются всем открытым вкладкам в реальном времени."""

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close()
            return

        self.contact_id = int(self.scope["url_route"]["kwargs"]["contact_id"])
        contact = await self._get_contact(user, self.contact_id)
        if contact is None:
            await self.close()
            return

        self.can_write = is_owner(user) or contact.responsible_id == user.id
        self.group = chat_group_name(self.contact_id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not getattr(self, "can_write", False):
            return
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            return
        text = (data.get("text") or "").strip()
        if not text:
            return

        activity = await self._send_outgoing(text)
        await abroadcast_activity(activity)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def _get_contact(self, user, contact_id):
        qs = Contact.objects.filter(organization=user.organization, pk=contact_id)
        return scope_claimable(qs, user).select_related("responsible").first()

    @database_sync_to_async
    def _send_outgoing(self, text):
        contact = Contact.objects.select_related("organization").get(pk=self.contact_id)
        return send_message(
            contact.organization, contact, Activity.Channel.TELEGRAM, text,
            self.scope["user"],
        )
