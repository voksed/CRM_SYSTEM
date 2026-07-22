from django.urls import path

from . import views

urlpatterns = [
    path("telegram/webhook/<int:account_id>/", views.telegram_webhook, name="telegram_webhook"),
    path("telegram/settings/", views.telegram_settings, name="telegram_settings"),
    path("telegram/", views.telegram_inbox, name="telegram_inbox"),
]
