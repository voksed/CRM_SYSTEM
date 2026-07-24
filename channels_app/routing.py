from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/contacts/<int:contact_id>/chat/", consumers.TelegramChatConsumer.as_asgi()),
]
