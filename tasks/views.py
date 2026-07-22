from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import is_owner, scope_to_owner_field
from accounts.services import get_or_create_organization
from audit.models import AuditLog
from audit.services import get_client_ip, log_action

from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    org = get_or_create_organization(request.user)
    tasks = Task.objects.filter(organization=org, is_done=False).select_related(
        "contact", "deal", "assigned_to"
    )
    tasks = scope_to_owner_field(tasks, request.user, field="assigned_to")
    return render(request, "tasks/list.html", {"tasks": tasks, "now": timezone.now()})


@login_required
def task_create(request):
    org = get_or_create_organization(request.user)
    if request.method == "POST":
        form = TaskForm(request.user, data=request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.organization = org
            if not is_owner(request.user):
                task.assigned_to = request.user
            task.save()
            log_action(
                request.user,
                AuditLog.Action.CREATED,
                obj=task,
                model_name="Задача",
                ip_address=get_client_ip(request),
            )
            return redirect("task_list")
    else:
        form = TaskForm(request.user, initial={"assigned_to": request.user})
    return render(request, "tasks/form.html", {"form": form})


@login_required
@require_POST
def task_toggle_done(request, task_id):
    org = get_or_create_organization(request.user)
    tasks = scope_to_owner_field(
        Task.objects.filter(organization=org), request.user, field="assigned_to"
    )
    task = get_object_or_404(tasks, pk=task_id)
    task.is_done = True
    task.completed_at = timezone.now()
    task.save(update_fields=["is_done", "completed_at"])
    log_action(
        request.user,
        AuditLog.Action.UPDATED,
        obj=task,
        model_name="Задача",
        object_repr=f"{task.title} (выполнено)",
        ip_address=get_client_ip(request),
    )
    return JsonResponse({"id": task.id, "is_done": task.is_done})
