from django.contrib import admin

from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("deal", "amount", "status", "due_date", "created_at")
    list_filter = ("organization", "status")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("deal", "amount", "method", "paid_at", "invoice")
    list_filter = ("organization", "method")
