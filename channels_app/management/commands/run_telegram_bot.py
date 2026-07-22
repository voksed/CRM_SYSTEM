import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand

from channels_app.models import TelegramAccount
from channels_app.services import receive_telegram_message


class Command(BaseCommand):
    help = (
        "Запускает aiogram long-polling для всех активных Telegram-ботов "
        "организаций одновременно. Процесс держит соединение открытым — "
        "останавливается по Ctrl+C. Для продакшена вместо этого используйте "
        "вебхук (channels_app.views.telegram_webhook)."
    )

    def handle(self, *args, **options):
        asyncio.run(self._run())

    async def _run(self):
        accounts = await sync_to_async(list)(
            TelegramAccount.objects.filter(is_active=True).select_related("organization")
        )
        if not accounts:
            self.stdout.write(self.style.WARNING("Нет активных Telegram-аккаунтов."))
            return

        bots = []
        token_to_org = {}
        for account in accounts:
            bots.append(Bot(token=account.bot_token))
            token_to_org[account.bot_token] = account.organization
            self.stdout.write(f"Бот подключён: {account.organization} ({account.bot_username})")

        dp = Dispatcher()

        @dp.message()
        async def handle_message(message: Message, bot: Bot):
            organization = token_to_org.get(bot.token)
            if organization is None or not message.text:
                return
            sender_name = ""
            if message.from_user:
                sender_name = " ".join(
                    filter(None, [message.from_user.first_name, message.from_user.last_name])
                )
            await sync_to_async(receive_telegram_message)(
                organization, str(message.chat.id), message.text, sender_name
            )

        self.stdout.write(
            self.style.SUCCESS(f"Запущено ботов: {len(bots)}. Остановка — Ctrl+C.")
        )
        await dp.start_polling(*bots)
