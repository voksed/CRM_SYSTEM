from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import scope_to_owner_field
from accounts.services import get_or_create_organization
from audit.models import AuditLog
from audit.services import get_client_ip, log_action
from deals.models import Deal

from .forms import PaymentForm
from .models import Invoice
from .services import calculate_balance


@login_required
def deal_billing(request, deal_id):
    org = get_or_create_organization(request.user)
    deals = scope_to_owner_field(Deal.objects.filter(organization=org), request.user)
    deal = get_object_or_404(deals, pk=deal_id)

    if request.method == "POST":
        form = PaymentForm(data=request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.organization = org
            payment.deal = deal
            payment.save()
            log_action(
                request.user,
                AuditLog.Action.CREATED,
                obj=payment,
                model_name="Оплата",
                object_repr=f"{payment.amount} сум по сделке «{deal.title}»",
                ip_address=get_client_ip(request),
            )
            return redirect("deal_billing", deal_id=deal.id)
    else:
        form = PaymentForm()

    context = {
        "deal": deal,
        "balance": calculate_balance(deal),
        "invoices": deal.invoices.all(),
        "payments": deal.payments.all(),
        "form": form,
    }
    return render(request, "billing/deal_detail.html", context)


@login_required
@require_POST
def issue_invoice(request, deal_id):
    org = get_or_create_organization(request.user)
    deals = scope_to_owner_field(Deal.objects.filter(organization=org), request.user)
    deal = get_object_or_404(deals, pk=deal_id)
    Invoice.objects.create(organization=org, deal=deal, amount=calculate_balance(deal))
    return redirect("deal_billing", deal_id=deal.id)


def invoice_public_view(request, token):
    invoice = get_object_or_404(Invoice, public_token=token)
    return render(request, "billing/invoice_public.html", {"invoice": invoice})
