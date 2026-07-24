from django.conf import settings
from django.db import models

from accounts.models import Organization
from contacts.models import Contact
from deals.models import Deal


DEFAULT_WELCOME = (
    "Здравствуйте! Напишите ваш вопрос сообщением — менеджер увидит его в CRM "
    "и ответит вам прямо здесь, в этом чате."
)
DEFAULT_HELP = (
    "Просто напишите сообщение — оно попадёт менеджеру в CRM, и он ответит вам "
    "в этом же чате. Команда /operator — если хотите отдельно позвать оператора."
)
DEFAULT_OPERATOR = (
    "Хорошо, передал менеджеру, что вам нужна помощь. Он ответит вам здесь "
    "в ближайшее время."
)
DEFAULT_LEAD_DONE = "Спасибо! Мы получили ваши ответы, менеджер скоро свяжется с вами."


class TelegramAccount(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="telegram_accounts"
    )
    title = models.CharField(
        max_length=100, blank=True, verbose_name="Название",
        help_text="Внутреннее имя бота, например «Основной» или «Поддержка».",
    )
    bot_token = models.CharField(max_length=200, verbose_name="Токен бота")
    bot_username = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Бот активен")
    last_update_id = models.PositiveBigIntegerField(default=0)

    welcome_text = models.TextField(
        blank=True, verbose_name="Приветствие (/start)",
        help_text="Оставьте пустым — будет использован текст по умолчанию.",
    )
    help_text_message = models.TextField(blank=True, verbose_name="Ответ на /help")
    operator_text = models.TextField(blank=True, verbose_name="Ответ на /operator")

    collect_lead = models.BooleanField(
        default=False, verbose_name="Собирать анкету лида",
        help_text="Бот задаст новому клиенту вопросы ниже и сохранит ответы в контакт.",
    )
    lead_done_text = models.TextField(
        blank=True, verbose_name="Сообщение после анкеты",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Telegram-бот"
        verbose_name_plural = "Telegram-боты"

    def __str__(self):
        label = self.title or self.bot_username
        return label or f"Telegram-бот организации {self.organization}"

    @property
    def welcome(self):
        return self.welcome_text or DEFAULT_WELCOME

    @property
    def help_message(self):
        return self.help_text_message or DEFAULT_HELP

    @property
    def operator_message(self):
        return self.operator_text or DEFAULT_OPERATOR

    @property
    def lead_done(self):
        return self.lead_done_text or DEFAULT_LEAD_DONE


class LeadQuestion(models.Model):
    """Вопрос анкеты, которую бот задаёт новому клиенту по шагам."""

    class Target(models.TextChoices):
        FULL_NAME = "full_name", "Имя клиента"
        PHONE = "phone", "Телефон"
        EMAIL = "email", "Email"
        NOTE = "note", "В заметку контакта"

    account = models.ForeignKey(
        TelegramAccount, on_delete=models.CASCADE, related_name="questions"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    text = models.CharField(max_length=255, verbose_name="Вопрос")
    target = models.CharField(
        max_length=20, choices=Target.choices, default=Target.NOTE,
        verbose_name="Куда сохранить ответ",
    )

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Вопрос анкеты"
        verbose_name_plural = "Вопросы анкеты"

    def __str__(self):
        return self.text


class LeadSession(models.Model):
    """Прогресс прохождения анкеты конкретным клиентом (простой DB-FSM)."""

    account = models.ForeignKey(
        TelegramAccount, on_delete=models.CASCADE, related_name="lead_sessions"
    )
    contact = models.ForeignKey(
        "contacts.Contact", on_delete=models.CASCADE, related_name="lead_sessions"
    )
    current_index = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("account", "contact")


class Activity(models.Model):
    class Type(models.TextChoices):
        CALL = "call", "Звонок"
        MESSAGE = "message", "Сообщение"
        EMAIL = "email", "Email"
        NOTE = "note", "Заметка"
        SYSTEM = "system", "Системное событие"

    class Channel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        MANUAL = "manual", "Вручную"

    class Direction(models.TextChoices):
        IN = "in", "Входящее"
        OUT = "out", "Исходящее"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="activities"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, null=True, blank=True, related_name="activities"
    )
    deal = models.ForeignKey(
        Deal, on_delete=models.CASCADE, null=True, blank=True, related_name="activities"
    )
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name="Тип")
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.MANUAL, verbose_name="Канал"
    )
    direction = models.CharField(
        max_length=10, choices=Direction.choices, blank=True, verbose_name="Направление"
    )
    text = models.TextField(blank=True, verbose_name="Текст")
    delivery_failed = models.BooleanField(default=False, verbose_name="Не доставлено")
    delivery_error = models.CharField(max_length=500, blank=True, verbose_name="Причина")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self):
        return f"{self.get_type_display()} ({self.get_channel_display()}) — {self.contact}"
