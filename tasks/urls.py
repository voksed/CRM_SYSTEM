from django.urls import path

from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("calendar/", views.task_calendar, name="task_calendar"),
    path("add/", views.task_create, name="task_create"),
    path("<int:task_id>/done/", views.task_toggle_done, name="task_toggle_done"),
]
