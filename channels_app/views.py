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
from .forms import TelegramSettingsForm
from .models import Activity, TelegramAccount
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
        receive_telegram_message(account.organization, chat_id, text, sender_name)

    return JsonResponse({"ok": True})


@login_required
@owner_required
def telegram_settings(request):
    org = get_or_create_organization(request.user)
    account, _ = TelegramAccount.objects.get_or_create(
        organization=org,
        defaults={
            "bot_token": settings.TELEGRAM_BOT_TOKEN_DEFAULT,
            "is_active": False,
        },
    )

    if request.method == "POST":
        form = TelegramSettingsForm(data=request.POST, instance=account)
        if form.is_valid():
            candidate = form.save(commit=False)
            try:
                candidate.bot_username = verify_bot_token(candidate.bot_token)
                register_bot_commands(candidate.bot_token)
            except ChannelNotConnected as exc:
                form.add_error("bot_token", str(exc))
            else:
                candidate.save()
                messages.success(request, f"Бот @{candidate.bot_username} подключён.")
                return redirect("telegram_settings")
    else:
        form = TelegramSettingsForm(instance=account)

    return render(
        request, "channels_app/telegram_settings.html", {"form": form, "account": account}
    )


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
