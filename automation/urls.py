from django.urls import path

from . import views

urlpatterns = [
    path("", views.rule_list, name="rule_list"),
    path("add/", views.rule_create, name="rule_create"),
    path("<int:rule_id>/delete/", views.rule_delete, name="rule_delete"),
]
