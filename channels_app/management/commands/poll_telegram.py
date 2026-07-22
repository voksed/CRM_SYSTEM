import requests
from django.core.management.base import BaseCommand

from channels_app.models import TelegramAccount
from channels_app.services import receive_telegram_message


class Command(BaseCommand):
    help = (
        "Опрашивает Telegram (long polling getUpdates) для всех подключённых "
        "ботов и заносит новые сообщения в CRM. Альтернатива вебхуку — удобна "
        "для локальной разработки/защиты диплома без публичного HTTPS-адреса. "
        "Предполагается периодический запуск (например, раз в 5–10 секунд)."
    )

    def handle(self, *args, **options):
        processed = 0
        for account in TelegramAccount.objects.filter(is_active=True):
            response = requests.get(
                f"https://api.telegram.org/bot{account.bot_token}/getUpdates",
                params={"offset": account.last_update_id + 1, "timeout": 5},
                timeout=15,
            )
            data = response.json()
            if not data.get("ok"):
                self.stderr.write(f"Ошибка Telegram API для {account}: {data}")
                continue

            for update in data.get("result", []):
                account.last_update_id = update["update_id"]
                message = update.get("message")
                if not message:
                    continue
                chat = message.get("chat", {})
                sender_name = " ".join(
                    filter(None, [chat.get("first_name"), chat.get("last_name")])
                ) or chat.get("username", "")
                receive_telegram_message(
                    account.organization,
                    str(chat.get("id")),
                    message.get("text", ""),
                    sender_name,
                )
                processed += 1

            account.save(update_fields=["last_update_id"])

        self.stdout.write(self.style.SUCCESS(f"Обработано новых сообщений: {processed}"))
