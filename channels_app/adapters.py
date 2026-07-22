import requests

from .models import Activity


class ChannelNotConnected(Exception):
    """Канал определён архитектурно, но реальный провайдер не подключён."""


class MessagingChannel:
    channel_code = None

    def send(self, contact, text: str) -> bool:
        raise NotImplementedError


class TelegramChannel(MessagingChannel):
    channel_code = Activity.Channel.TELEGRAM

    def __init__(self, organization):
        self.organization = organization

    def send(self, contact, text: str) -> bool:
        account = getattr(self.organization, "telegram_account", None)
        if not account or not account.is_active:
            raise ChannelNotConnected("Telegram-бот не подключён для этой организации.")
        if not contact.telegram_chat_id:
            raise ChannelNotConnected("У контакта нет привязанного Telegram-чата.")

        response = requests.post(
            f"https://api.telegram.org/bot{account.bot_token}/sendMessage",
            json={"chat_id": contact.telegram_chat_id, "text": text},
            timeout=10,
        )
        return response.ok


class WhatsAppChannel(MessagingChannel):
    channel_code = Activity.Channel.WHATSAPP

    def send(self, contact, text: str) -> bool:
        raise ChannelNotConnected(
            "WhatsApp Business API требует верификации бизнеса в Meta — "
            "не подключено в рамках дипломного проекта. Реализуйте send() здесь "
            "при подключении провайдера (архитектура уже готова к этому)."
        )


class VKChannel(MessagingChannel):
    channel_code = Activity.Channel.VK

    def send(self, contact, text: str) -> bool:
        raise ChannelNotConnected(
            "Интеграция с VK API требует регистрации сообщества/приложения — "
            "не подключено в рамках дипломного проекта."
        )


class PhoneChannel(MessagingChannel):
    channel_code = Activity.Channel.PHONE

    def send(self, contact, text: str) -> bool:
        raise ChannelNotConnected(
            "Телефония требует подключения SIP/облачной АТС провайдера — "
            "не подключено в рамках дипломного проекта."
        )


_ADAPTERS = {
    Activity.Channel.TELEGRAM: TelegramChannel,
    Activity.Channel.WHATSAPP: WhatsAppChannel,
    Activity.Channel.VK: VKChannel,
    Activity.Channel.PHONE: PhoneChannel,
}


def get_channel(channel_code, organization):
    adapter_cls = _ADAPTERS.get(channel_code)
    if adapter_cls is None:
        raise ChannelNotConnected(f"Неизвестный канал: {channel_code}")
    return adapter_cls(organization) if channel_code == Activity.Channel.TELEGRAM else adapter_cls()
