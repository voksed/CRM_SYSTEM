import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.permissions import owner_required, scope_claimable
from accounts.services import get_or_create_organization
from contacts.models import Contact

from .adapters import ChannelNotConnected, register_bot_commands, verify_bot_token
from .forms import LeadQuestionFormSet, TelegramSettingsForm
from .models import Activity, TelegramAccount
from .realtime import broadcast_activity
from .services import receive_telegram_message


@csrf_exempt
@require_POST
def telegram_webhook(request, account_id):
    account = get_object_or_404(TelegramAccount, pk=account_id, is_active=True)
    payload = json.loads(request.body or "{}")
    message = payload.get("message") or payload.get("edited_message")

    if message:
        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        text = message.get("text", "")
        sender_name = " ".join(
            filter(None, [chat.get("first_name"), chat.get("last_name")])
        ) or chat.get("username", "")
        activity, _ = receive_telegram_message(account, chat_id, text, sender_name)
        broadcast_activity(activity)

    return JsonResponse({"ok": True})


@login_required
@owner_required
def telegram_settings(request):
    org = get_or_create_organization(request.user)
    accounts = org.telegram_accounts.all().order_by("-is_active", "title", "id")
    return render(
        request,
        "channels_app/telegram_settings.html",
        {"accounts": accounts, "default_token": settings.TELEGRAM_BOT_TOKEN_DEFAULT},
    )


@login_required
@owner_required
def telegram_bot_form(request, account_id=None):
    org = get_or_create_organization(request.user)
    if account_id:
        account = get_object_or_404(TelegramAccount, pk=account_id, organization=org)
    else:
        account = TelegramAccount(
            organization=org, bot_token=settings.TELEGRAM_BOT_TOKEN_DEFAULT
        )

    if request.method == "POST":
        form = TelegramSettingsForm(data=request.POST, instance=account)
        formset = LeadQuestionFormSet(data=request.POST, instance=account)
        if form.is_valid() and formset.is_valid():
            candidate = form.save(commit=False)
            candidate.organization = org
            token_changed = "bot_token" in form.changed_data or not account.pk
            try:
                if token_changed or not candidate.bot_username:
                    candidate.bot_username = verify_bot_token(candidate.bot_token)
                    register_bot_commands(candidate.bot_token)
            except ChannelNotConnected as exc:
                form.add_error("bot_token", str(exc))
            else:
                candidate.save()
                formset.instance = candidate
                formset.save()
                messages.success(request, f"Бот @{candidate.bot_username} сохранён.")
                return redirect("telegram_settings")
    else:
        form = TelegramSettingsForm(instance=account)
        formset = LeadQuestionFormSet(instance=account)

    return render(
        request,
        "channels_app/telegram_bot_form.html",
        {"form": form, "formset": formset, "account": account, "is_new": not account.pk},
    )


@login_required
@owner_required
@require_POST
def telegram_bot_delete(request, account_id):
    org = get_or_create_organization(request.user)
    account = get_object_or_404(TelegramAccount, pk=account_id, organization=org)
    account.delete()
    messages.success(request, "Бот удалён.")
    return redirect("telegram_settings")


@login_required
def telegram_inbox(request):
    org = get_or_create_organization(request.user)

    last_message = Activity.objects.filter(
        contact=OuterRef("pk"), channel=Activity.Channel.TELEGRAM
    ).order_by("-created_at")

    contacts = (
        Contact.objects.filter(organization=org)
        .exclude(telegram_chat_id="")
        .annotate(
            last_message_at=Subquery(last_message.values("created_at")[:1]),
            last_message_text=Subquery(last_message.values("text")[:1]),
            last_message_direction=Subquery(last_message.values("direction")[:1]),
        )
        .order_by("-last_message_at")
    )
    contacts = scope_claimable(contacts, request.user)

    return render(request, "channels_app/telegram_inbox.html", {"contacts": contacts})
