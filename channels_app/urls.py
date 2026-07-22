from django.urls import path

from . import views

urlpatterns = [
    path("telegram/webhook/<int:account_id>/", views.telegram_webhook, name="telegram_webhook"),
]
