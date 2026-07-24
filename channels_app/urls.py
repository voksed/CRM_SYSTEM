from django.urls import path

from . import views

urlpatterns = [
    path("telegram/webhook/<int:account_id>/", views.telegram_webhook, name="telegram_webhook"),
    path("telegram/settings/", views.telegram_settings, name="telegram_settings"),
    path("telegram/settings/add/", views.telegram_bot_form, name="telegram_bot_create"),
    path(
        "telegram/settings/<int:account_id>/",
        views.telegram_bot_form,
        name="telegram_bot_edit",
    ),
    path(
        "telegram/settings/<int:account_id>/delete/",
        views.telegram_bot_delete,
        name="telegram_bot_delete",
    ),
    path("telegram/", views.telegram_inbox, name="telegram_inbox"),
]
