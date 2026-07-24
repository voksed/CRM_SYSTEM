"""
ASGI config for config project.

Маршрутизирует HTTP (Django), WebSocket (Channels) и lifespan, внутри которого
поднимается Telegram-бот — в том же процессе, что и WebSocket-сервер, чтобы
входящие сообщения тут же уходили в браузер через слой каналов.
"""

import logging
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализируем Django ДО импорта consumer'ов и рантайма бота (им нужны модели).
# ASGIStaticFilesHandler отдаёт /static/ при DEBUG — без него чистый ASGI-сервер
# (uvicorn) не обслуживает статику, и стили/скрипты не подгружаются.
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # noqa: E402

django_asgi_app = ASGIStaticFilesHandler(get_asgi_application())

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from channels_app.routing import websocket_urlpatterns  # noqa: E402
from channels_app.telegram_runtime import TelegramBotRuntime  # noqa: E402

logger = logging.getLogger(__name__)

_bot_runtime = TelegramBotRuntime()


async def lifespan_app(scope, receive, send):
    """Стартует/останавливает Telegram-бот по сигналам ASGI-сервера (uvicorn)."""
    while True:
        message = await receive()
        if message["type"] == "lifespan.startup":
            try:
                await _bot_runtime.start()
            except Exception as exc:  # noqa: BLE001 — сервер должен подняться в любом случае
                logger.exception("Не удалось запустить Telegram-бот: %s", exc)
                await send({"type": "lifespan.startup.failed", "message": str(exc)})
            else:
                await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            try:
                await _bot_runtime.stop()
            except Exception:  # noqa: BLE001
                logger.exception("Ошибка при остановке Telegram-бота")
            await send({"type": "lifespan.shutdown.complete"})
            return


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        "lifespan": lifespan_app,
    }
)
