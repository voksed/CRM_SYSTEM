from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import owner_required
from accounts.services import get_or_create_organization
from audit.models import AuditLog
from audit.services import get_client_ip, log_action

from .forms import AutomationRuleForm
from .models import AutomationRule


@login_required
@owner_required
def rule_list(request):
    org = get_or_create_organization(request.user)
    rules = AutomationRule.objects.filter(organization=org)
    return render(request, "automation/list.html", {"rules": rules})


@login_required
@owner_required
def rule_create(request):
    org = get_or_create_organization(request.user)
    if request.method == "POST":
        form = AutomationRuleForm(org, data=request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.organization = org
            rule.save()
            log_action(
                request.user,
                AuditLog.Action.CREATED,
                obj=rule,
                model_name="Правило автоматизации",
                ip_address=get_client_ip(request),
            )
            return redirect("rule_list")
    else:
        form = AutomationRuleForm(org)
    return render(request, "automation/form.html", {"form": form})


@login_required
@owner_required
@require_POST
def rule_delete(request, rule_id):
    org = get_or_create_organization(request.user)
    rule = get_object_or_404(AutomationRule, pk=rule_id, organization=org)
    log_action(
        request.user,
        AuditLog.Action.DELETED,
        obj=rule,
        model_name="Правило автоматизации",
        ip_address=get_client_ip(request),
    )
    rule.delete()
    return redirect("rule_list")
