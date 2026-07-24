import calendar as _calendar
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import is_owner, scope_to_owner_field
from accounts.services import get_or_create_organization
from audit.models import AuditLog
from audit.services import get_client_ip, log_action
from notifications.models import Notification
from notifications.services import notify

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
            notify(
                task.assigned_to,
                f"Новая задача: {task.title}",
                text=f"Срок — {task.due_at:%d.%m.%Y %H:%M}",
                url=reverse("task_list"),
                kind=Notification.Kind.TASK,
                actor=request.user,
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


MONTH_NAMES_RU = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
WEEKDAY_NAMES_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


@login_required
def task_calendar(request):
    """Помесячный календарь запланированных задач и встреч сотрудника."""
    org = get_or_create_organization(request.user)
    today = timezone.localdate()

    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        if not 1 <= month <= 12:
            raise ValueError
    except (TypeError, ValueError):
        year, month = today.year, today.month

    tasks = Task.objects.filter(
        organization=org,
        due_at__year=year,
        due_at__month=month,
    ).select_related("contact", "deal", "assigned_to")
    tasks = scope_to_owner_field(tasks, request.user, field="assigned_to")

    tasks_by_day = {}
    for task in tasks.order_by("due_at"):
        day = timezone.localtime(task.due_at).day
        tasks_by_day.setdefault(day, []).append(task)

    cal = _calendar.Calendar(firstweekday=0)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        cells = []
        for cell_date in week:
            in_month = cell_date.month == month
            cells.append({
                "date": cell_date,
                "day": cell_date.day,
                "in_month": in_month,
                "is_today": cell_date == today,
                "tasks": tasks_by_day.get(cell_date.day, []) if in_month else [],
            })
        weeks.append(cells)

    prev_month = date(year, month, 1) - timedelta(days=1)
    next_month = date(year, month, 28) + timedelta(days=10)

    context = {
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES_RU[month],
        "weekday_names": WEEKDAY_NAMES_RU,
        "weeks": weeks,
        "prev_year": prev_month.year,
        "prev_month": prev_month.month,
        "next_year": next_month.year,
        "next_month": next_month.month,
        "today": today,
    }
    return render(request, "tasks/calendar.html", context)
