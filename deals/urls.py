from django.urls import path

from . import views

urlpatterns = [
    path("", views.kanban_board, name="kanban_board"),
    path("add/", views.deal_create, name="deal_create"),
    path("<int:deal_id>/move/", views.deal_move, name="deal_move"),
]
