import asyncio

from django.core.management.base import BaseCommand

from channels_app.telegram_runtime import TelegramBotRuntime


class Command(BaseCommand):
    help = (
        "Запускает aiogram long-polling для всех активных Telegram-ботов "
        "организаций отдельным процессом. Держит соединение открытым — "
        "останавливается по Ctrl+C.\n\n"
        "ВНИМАНИЕ: при in-memory слое каналов (по умолчанию) отдельный процесс "
        "НЕ доставляет сообщения в WebSocket веб-сервера. Для real-time чата "
        "запускайте проект через `daphne config.asgi:application` — там бот "
        "стартует внутри веб-процесса автоматически. Отдельная команда нужна "
        "только для схемы с channels_redis или чистой отладки приёма сообщений."
    )

    def handle(self, *args, **options):
        asyncio.run(self._run())

    async def _run(self):
        runtime = TelegramBotRuntime()
        await runtime.start()
        if not runtime._bots:
            self.stdout.write(self.style.WARNING("Нет активных Telegram-аккаунтов."))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"Запущено ботов: {len(runtime._bots)}. Остановка — Ctrl+C."
            )
        )
        try:
            await runtime._task
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await runtime.stop()
