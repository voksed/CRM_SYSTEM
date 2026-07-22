import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import TelegramAccount
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
