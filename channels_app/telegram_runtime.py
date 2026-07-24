"""Единая точка запуска Telegram-ботов организаций (aiogram long-polling).

Поддерживает несколько ботов одновременно, у каждого — свои тексты приветствий
и своя анкета для сбора лида (пошаговый опрос, ответы сохраняются в контакт).

Используется и из management-команды `run_telegram_bot`, и из ASGI-lifespan
(config.asgi), чтобы бот работал внутри того же процесса, что и WebSocket-сервер.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command as CommandFilter
from aiogram.filters import CommandStart
from aiogram.types import Message
from asgiref.sync import sync_to_async
from django.utils import timezone

from contacts.models import Contact

from .adapters import BOT_COMMANDS
from .models import Activity, LeadSession, TelegramAccount
from .realtime import abroadcast_activity
from .services import receive_telegram_message, send_message

logger = logging.getLogger(__name__)


def _sender_name(message: Message) -> str:
    if not message.from_user:
        return ""
    return " ".join(
        filter(None, [message.from_user.first_name, message.from_user.last_name])
    )


# --- Синхронные помощники (работают с БД, вызываются через sync_to_async) ------


def _flag_operator_request(account, contact):
    from tasks.models import Task

    organization = account.organization
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


def _apply_answer(contact, question, text):
    text = (text or "").strip()
    Target = question.Target
    if question.target == Target.FULL_NAME:
        contact.full_name = text[:255]
        contact.save(update_fields=["full_name"])
    elif question.target == Target.PHONE:
        contact.phone = text[:32]
        contact.save(update_fields=["phone"])
    elif question.target == Target.EMAIL:
        contact.email = text[:254]
        contact.save(update_fields=["email"])
    else:  # NOTE
        line = f"{question.text}: {text}"
        contact.notes = (contact.notes + "\n" if contact.notes else "") + line
        contact.save(update_fields=["notes"])


def _finalize_lead(account, contact):
    from django.urls import reverse

    from notifications.models import Notification
    from notifications.services import notify
    from tasks.models import Task

    if contact.status == Contact.Status.NEW:
        contact.status = Contact.Status.IN_PROGRESS
        contact.save(update_fields=["status"])

    assignee = contact.responsible or account.organization.owner
    if assignee is None:
        return
    Task.objects.create(
        organization=account.organization,
        contact=contact,
        assigned_to=assignee,
        task_type=Task.Type.FOLLOW_UP,
        title=f"Новый лид из Telegram: {contact.full_name}",
        due_at=timezone.now(),
        is_auto_generated=True,
    )
    notify(
        assignee,
        f"Новый лид заполнил анкету: {contact.full_name}",
        text="Клиент ответил на вопросы бота в Telegram.",
        url=reverse("contact_detail", args=[contact.id]),
        kind=Notification.Kind.CONTACT,
    )


def _send_out_sync(account, contact, text):
    """Отправляет сообщение клиенту через бота и логирует его как исходящее.
    Возвращает Activity для последующей трансляции в WebSocket."""
    return send_message(
        account.organization, contact, Activity.Channel.TELEGRAM, text, None
    )


def _start_form(account, contact):
    """(Пере)запускает анкету. Возвращает Activity первого вопроса или None."""
    if not account.collect_lead:
        return None
    questions = list(account.questions.all())
    if not questions:
        return None
    LeadSession.objects.update_or_create(
        account=account,
        contact=contact,
        defaults={"current_index": 0, "is_completed": False},
    )
    return _send_out_sync(account, contact, questions[0].text)


def _advance_form(account, activity, text, created):
    """Продвигает анкету на один шаг. Возвращает Activity ответа бота
    (следующий вопрос или финальное сообщение) либо None."""
    contact = activity.contact
    session = LeadSession.objects.filter(
        account=account, contact=contact, is_completed=False
    ).first()

    if session is None:
        # новому контакту, не нажавшему /start, тоже предлагаем анкету
        if created:
            return _start_form(account, contact)
        return None

    questions = list(account.questions.all())
    if session.current_index < len(questions):
        _apply_answer(contact, questions[session.current_index], text)
        session.current_index += 1

    if session.current_index >= len(questions):
        session.is_completed = True
        session.save(update_fields=["current_index", "is_completed"])
        _finalize_lead(account, contact)
        return _send_out_sync(account, contact, account.lead_done)

    session.save(update_fields=["current_index"])
    return _send_out_sync(account, contact, questions[session.current_index].text)


# --- Диспетчер и обработчики ---------------------------------------------------


def build_dispatcher(token_to_account: dict) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def handle_start(message: Message, bot: Bot):
        account = token_to_account.get(bot.token)
        if account is None:
            return
        activity, _ = await sync_to_async(receive_telegram_message)(
            account, str(message.chat.id), "/start", _sender_name(message)
        )
        await abroadcast_activity(activity)
        await message.answer(account.welcome)
        out = await sync_to_async(_start_form)(account, activity.contact)
        if out is not None:
            await abroadcast_activity(out)

    @dp.message(CommandFilter("help"))
    async def handle_help(message: Message, bot: Bot):
        account = token_to_account.get(bot.token)
        await message.answer(account.help_message if account else "")

    @dp.message(CommandFilter("operator"))
    async def handle_operator(message: Message, bot: Bot):
        account = token_to_account.get(bot.token)
        if account is None:
            return
        activity, _ = await sync_to_async(receive_telegram_message)(
            account, str(message.chat.id), "/operator (просит оператора)",
            _sender_name(message),
        )
        await abroadcast_activity(activity)
        await sync_to_async(_flag_operator_request)(account, activity.contact)
        await message.answer(account.operator_message)

    @dp.message(F.text)
    async def handle_message(message: Message, bot: Bot):
        account = token_to_account.get(bot.token)
        if account is None:
            return
        activity, created = await sync_to_async(receive_telegram_message)(
            account, str(message.chat.id), message.text, _sender_name(message)
        )
        await abroadcast_activity(activity)
        out = await sync_to_async(_advance_form)(account, activity, message.text, created)
        if out is not None:
            await abroadcast_activity(out)

    return dp


async def _build_bots():
    accounts = await sync_to_async(list)(
        TelegramAccount.objects.filter(is_active=True).select_related("organization")
    )
    bots = []
    token_to_account = {}
    for account in accounts:
        bot = Bot(token=account.bot_token)
        try:
            await bot.set_my_commands(BOT_COMMANDS)
        except Exception as exc:  # noqa: BLE001 — не валим запуск из-за одного бота
            logger.warning("Не удалось зарегистрировать команды бота: %s", exc)
        bots.append(bot)
        token_to_account[account.bot_token] = account
    return bots, token_to_account


class TelegramBotRuntime:
    """Управляет фоновым long-polling внутри ASGI-процесса (start/stop по
    сигналам lifespan)."""

    def __init__(self):
        self._task = None
        self._dp = None
        self._bots = []

    async def start(self):
        self._bots, token_to_account = await _build_bots()
        if not self._bots:
            logger.info("Нет активных Telegram-аккаунтов — бот не запущен.")
            return
        self._dp = build_dispatcher(token_to_account)
        self._task = asyncio.create_task(
            self._dp.start_polling(*self._bots, handle_signals=False)
        )
        self._task.add_done_callback(self._on_polling_done)
        logger.warning("Telegram-бот(ы) запущены в ASGI-процессе: %s", len(self._bots))

    @staticmethod
    def _on_polling_done(task):
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.error("Telegram long-polling упал: %r", exc, exc_info=exc)

    async def stop(self):
        if self._dp is not None:
            try:
                await self._dp.stop_polling()
            except Exception:  # noqa: BLE001
                pass
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        for bot in self._bots:
            try:
                await bot.session.close()
            except Exception:  # noqa: BLE001
                pass
        self._task = None
        self._dp = None
        self._bots = []
