from django.urls import path

from . import views

urlpatterns = [
    path("<int:deal_id>/", views.deal_billing, name="deal_billing"),
    path("<int:deal_id>/invoice/", views.issue_invoice, name="issue_invoice"),
    path("invoice/<uuid:token>/", views.invoice_public_view, name="invoice_public"),
]
