from aiogram import Bot
from asgiref.sync import async_to_sync

from .models import Activity


class ChannelNotConnected(Exception):
    """Telegram-бот не подключён или отклонил запрос."""


class TelegramChannel:
    channel_code = Activity.Channel.TELEGRAM

    def __init__(self, organization):
        self.organization = organization

    def send(self, contact, text: str) -> bool:
        account = getattr(self.organization, "telegram_account", None)
        if not account or not account.is_active:
            raise ChannelNotConnected("Telegram-бот не подключён для этой организации.")
        if not contact.telegram_chat_id:
            raise ChannelNotConnected("У контакта нет привязанного Telegram-чата.")

        async def _send():
            bot = Bot(token=account.bot_token)
            try:
                await bot.send_message(chat_id=contact.telegram_chat_id, text=text)
            finally:
                await bot.session.close()

        try:
            async_to_sync(_send)()
        except ChannelNotConnected:
            raise
        except Exception as exc:
            raise ChannelNotConnected(f"Telegram API отклонил сообщение: {exc}") from exc
        return True


def get_channel(channel_code, organization):
    if channel_code != Activity.Channel.TELEGRAM:
        raise ChannelNotConnected(f"Отправка через канал «{channel_code}» не поддерживается.")
    return TelegramChannel(organization)


def verify_bot_token(token: str) -> str:
    """Проверяет токен через Telegram API (getMe) и возвращает username бота.
    Бросает ChannelNotConnected, если токен недействителен."""

    async def _get_me():
        bot = Bot(token=token)
        try:
            me = await bot.get_me()
        finally:
            await bot.session.close()
        return me

    try:
        me = async_to_sync(_get_me)()
    except Exception as exc:
        raise ChannelNotConnected(f"Telegram отклонил токен: {exc}") from exc
    return me.username
