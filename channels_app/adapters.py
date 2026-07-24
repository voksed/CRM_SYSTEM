from aiogram import Bot
from aiogram.types import BotCommand
from asgiref.sync import async_to_sync

from .models import Activity

# Меню быстрых команд Telegram (кнопка "/" в чате с ботом). Используется и при
# сохранении токена в настройках, и при запуске run_telegram_bot — регистрация
# идемпотентна, повторный вызов просто переустанавливает тот же список.
BOT_COMMANDS = [
    BotCommand(command="start", description="Начать общение"),
    BotCommand(command="help", description="Как это работает"),
    BotCommand(command="operator", description="Позвать оператора"),
]


class ChannelNotConnected(Exception):
    """Telegram-бот не подключён или отклонил запрос."""


class TelegramChannel:
    channel_code = Activity.Channel.TELEGRAM

    def __init__(self, organization):
        self.organization = organization

    def send(self, contact, text: str) -> bool:
        account = contact.telegram_account
        if account is None or not account.is_active:
            account = self.organization.telegram_accounts.filter(is_active=True).first()
        if account is None:
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
            text_exc = str(exc).lower()
            if "chat not found" in text_exc or "bot was blocked" in text_exc:
                raise ChannelNotConnected(
                    "Клиент ещё не начал диалог с ботом (или заблокировал его). "
                    "Написать первым может только он: пусть отправит боту любое "
                    "сообщение — после этого вы сможете отвечать."
                ) from exc
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


def register_bot_commands(token: str) -> None:
    """Регистрирует меню быстрых команд (/start, /help, /operator) у бота —
    после этого команды сразу видны клиенту в Telegram."""

    async def _register():
        bot = Bot(token=token)
        try:
            await bot.set_my_commands(BOT_COMMANDS)
        finally:
            await bot.session.close()

    async_to_sync(_register)()
