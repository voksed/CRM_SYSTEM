import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command as CommandFilter
from aiogram.filters import CommandStart
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.utils import timezone

from channels_app.adapters import BOT_COMMANDS
from channels_app.models import TelegramAccount
from channels_app.services import receive_telegram_message
from tasks.models import Task

WELCOME_TEXT = (
    "Здравствуйте! Напишите ваш вопрос сообщением — менеджер увидит его в CRM "
    "и ответит вам прямо здесь, в этом чате."
)
HELP_TEXT = (
    "Просто напишите сообщение — оно попадёт менеджеру в CRM, и он ответит вам "
    "в этом же чате. Команда /operator — если хотите отдельно позвать оператора."
)
OPERATOR_TEXT = (
    "Хорошо, передал менеджеру, что вам нужна помощь. Он ответит вам здесь "
    "в ближайшее время."
)


def _sender_name(message: Message) -> str:
    if not message.from_user:
        return ""
    return " ".join(
        filter(None, [message.from_user.first_name, message.from_user.last_name])
    )


def _flag_operator_request(organization, contact):
    assignee = contact.responsible or organization.owner
    if assignee is None:
        return
    Task.objects.create(
        organization=organization,
        contact=contact,
        assigned_to=assignee,
        task_type=Task.Type.OTHER,
        title=f"{contact.full_name} просит оператора в Telegram",
        due_at=timezone.now(),
        is_auto_generated=True,
    )


class Command(BaseCommand):
    help = (
        "Запускает aiogram long-polling для всех активных Telegram-ботов "
        "организаций одновременно. Регистрирует меню команд (/start, /help, "
        "/operator) и держит соединение открытым — останавливается по Ctrl+C. "
        "Для продакшена вместо этого используйте вебхук "
        "(channels_app.views.telegram_webhook)."
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
            bot = Bot(token=account.bot_token)
            await bot.set_my_commands(BOT_COMMANDS)
            bots.append(bot)
            token_to_org[account.bot_token] = account.organization
            self.stdout.write(f"Бот подключён: {account.organization} ({account.bot_username})")

        dp = Dispatcher()

        @dp.message(CommandStart())
        async def handle_start(message: Message, bot: Bot):
            organization = token_to_org.get(bot.token)
            if organization is None:
                return
            await sync_to_async(receive_telegram_message)(
                organization, str(message.chat.id), "/start", _sender_name(message)
            )
            await message.answer(WELCOME_TEXT)

        @dp.message(CommandFilter("help"))
        async def handle_help(message: Message):
            await message.answer(HELP_TEXT)

        @dp.message(CommandFilter("operator"))
        async def handle_operator(message: Message, bot: Bot):
            organization = token_to_org.get(bot.token)
            if organization is None:
                return
            contact = await sync_to_async(receive_telegram_message)(
                organization,
                str(message.chat.id),
                "/operator (просит оператора)",
                _sender_name(message),
            )
            await sync_to_async(_flag_operator_request)(organization, contact)
            await message.answer(OPERATOR_TEXT)

        @dp.message(F.text)
        async def handle_message(message: Message, bot: Bot):
            organization = token_to_org.get(bot.token)
            if organization is None:
                return
            await sync_to_async(receive_telegram_message)(
                organization, str(message.chat.id), message.text, _sender_name(message)
            )

        self.stdout.write(
            self.style.SUCCESS(f"Запущено ботов: {len(bots)}. Остановка — Ctrl+C.")
        )
        await dp.start_polling(*bots)
