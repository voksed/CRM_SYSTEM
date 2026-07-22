from django.urls import path

from . import views

urlpatterns = [
    path("", views.contact_list, name="contact_list"),
    path("add/", views.contact_create, name="contact_create"),
    path("<int:contact_id>/", views.contact_detail, name="contact_detail"),
    path("<int:contact_id>/edit/", views.contact_update, name="contact_update"),
    path("<int:contact_id>/delete/", views.contact_delete, name="contact_delete"),
    path("<int:contact_id>/log/", views.contact_log_activity, name="contact_log_activity"),
    path("<int:contact_id>/send/", views.contact_send_message, name="contact_send_message"),
]
