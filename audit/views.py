from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from accounts.models import User
from accounts.permissions import owner_required
from accounts.services import get_or_create_organization

from .models import AuditLog


@login_required
@owner_required
def audit_log_list(request):
    org = get_or_create_organization(request.user)
    logs = AuditLog.objects.filter(organization=org).select_related("actor")

    action = request.GET.get("action")
    if action:
        logs = logs.filter(action=action)

    actor_id = request.GET.get("actor")
    if actor_id:
        logs = logs.filter(actor_id=actor_id)

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "actions": AuditLog.Action.choices,
        "members": User.objects.filter(organization=org),
        "active_action": action,
        "active_actor": actor_id,
    }
    return render(request, "audit/list.html", context)
