from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import is_owner, scope_to_owner_field
from accounts.services import get_or_create_organization
from audit.models import AuditLog
from audit.services import get_client_ip, log_action
from contacts.models import Contact

from .forms import DealForm
from .models import Deal, Stage


@login_required
def kanban_board(request):
    org = get_or_create_organization(request.user)
    pipeline = org.pipelines.first()

    stages = []
    deals_by_stage = {}
    if pipeline:
        stages = list(pipeline.stages.all())
        deals = Deal.objects.filter(organization=org).select_related("contact")
        deals = scope_to_owner_field(deals, request.user)
        deals_by_stage = defaultdict(list)
        for deal in deals:
            deals_by_stage[deal.stage_id].append(deal)

    context = {"pipeline": pipeline, "stages": stages, "deals_by_stage": deals_by_stage}
    return render(request, "deals/kanban.html", context)


@login_required
def deal_create(request):
    org = get_or_create_organization(request.user)
    contacts = scope_to_owner_field(Contact.objects.filter(organization=org), request.user)
    initial = {}
    contact_id = request.GET.get("contact")
    if contact_id:
        initial["contact"] = get_object_or_404(contacts, pk=contact_id)

    if request.method == "POST":
        form = DealForm(request.user, data=request.POST)
        if form.is_valid():
            deal = form.save(commit=False)
            deal.organization = org
            deal.pipeline = deal.stage.pipeline
            if not is_owner(request.user):
                deal.responsible = request.user
            deal.save()
            log_action(
                request.user,
                AuditLog.Action.CREATED,
                obj=deal,
                model_name="Сделка",
                ip_address=get_client_ip(request),
            )
            return redirect("kanban_board")
    else:
        pipeline = org.pipelines.first()
        first_stage = pipeline.stages.first() if pipeline else None
        if first_stage:
            initial["stage"] = first_stage
        form = DealForm(request.user, initial=initial)
    return render(request, "deals/form.html", {"form": form})


@login_required
@require_POST
def deal_move(request, deal_id):
    org = get_or_create_organization(request.user)
    deals = scope_to_owner_field(Deal.objects.filter(organization=org), request.user)
    deal = get_object_or_404(deals, pk=deal_id)
    stage = get_object_or_404(Stage, pk=request.POST.get("stage_id"), pipeline__organization=org)
    old_stage_name = deal.stage.name
    deal.stage = stage
    deal.save()
    log_action(
        request.user,
        AuditLog.Action.MOVED,
        obj=deal,
        model_name="Сделка",
        object_repr=f"{deal.title}: «{old_stage_name}» → «{stage.name}»",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"id": deal.id, "stage_id": deal.stage_id, "status": deal.status})
