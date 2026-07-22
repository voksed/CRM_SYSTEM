from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from audit.models import AuditLog
from audit.services import get_client_ip, log_action
from contacts.models import Contact
from deals.models import Deal
from tasks.models import Task

from .forms import ManagerInviteForm, ProfileForm, RussianPasswordChangeForm, TeamMemberForm
from .models import User
from .permissions import is_owner, owner_required
from .services import get_or_create_organization


@login_required
def dashboard(request):
    org = get_or_create_organization(request.user)

    open_deals = Deal.objects.filter(organization=org, status=Deal.Status.OPEN)
    contacts = Contact.objects.filter(organization=org)
    if not is_owner(request.user):
        open_deals = open_deals.filter(responsible=request.user)
        contacts = contacts.filter(responsible=request.user)

    open_deals_amount = open_deals.aggregate(total=Sum("amount"))["total"] or 0

    my_tasks = Task.objects.filter(
        organization=org,
        assigned_to=request.user,
        is_done=False,
        due_at__date__lte=timezone.localdate(),
    ).order_by("due_at")[:10]

    context = {
        "open_deals_count": open_deals.count(),
        "open_deals_amount": open_deals_amount,
        "contacts_count": contacts.count(),
        "my_tasks": my_tasks,
    }
    return render(request, "dashboard.html", context)


@login_required
def analytics_dashboard(request):
    org = get_or_create_organization(request.user)
    owner_view = is_owner(request.user)

    pipeline = org.pipelines.first()
    if pipeline:
        stage_deal_filter = Q() if owner_view else Q(deals__responsible=request.user)
        stages = pipeline.stages.annotate(
            deals_count=Count("deals", filter=stage_deal_filter)
        )
    else:
        stages = []

    deals = Deal.objects.filter(organization=org)
    if not owner_view:
        deals = deals.filter(responsible=request.user)

    total_deals = deals.count()
    won_deals = deals.filter(status=Deal.Status.WON)
    won_count = won_deals.count()
    lost_count = deals.filter(status=Deal.Status.LOST).count()
    conversion_rate = round(won_count / total_deals * 100, 1) if total_deals else 0

    manager_stats = None
    if owner_view:
        manager_stats = User.objects.filter(organization=org).annotate(
            deals_count=Count("deals", distinct=True),
            revenue=Sum("deals__amount", filter=Q(deals__status=Deal.Status.WON)),
            activities_count=Count("activities", distinct=True),
        )

    revenue_by_source = (
        won_deals.values("contact__source")
        .annotate(revenue=Sum("amount"), deals_count=Count("id"))
        .order_by("-revenue")
    )
    source_labels = dict(Contact.Source.choices)

    context = {
        "owner_view": owner_view,
        "stages": stages,
        "total_deals": total_deals,
        "won_count": won_count,
        "lost_count": lost_count,
        "conversion_rate": conversion_rate,
        "manager_stats": manager_stats,
        "revenue_by_source": [
            {
                "label": source_labels.get(row["contact__source"], row["contact__source"]),
                "revenue": row["revenue"],
                "deals_count": row["deals_count"],
            }
            for row in revenue_by_source
        ],
    }
    return render(request, "analytics.html", context)


@login_required
@owner_required
def team_list(request):
    org = get_or_create_organization(request.user)
    members = User.objects.filter(organization=org).order_by("-role", "username")
    return render(request, "accounts/team_list.html", {"members": members})


@login_required
@owner_required
def team_create(request):
    org = get_or_create_organization(request.user)
    if request.method == "POST":
        form = ManagerInviteForm(data=request.POST)
        if form.is_valid():
            manager = form.save(organization=org)
            log_action(
                request.user,
                AuditLog.Action.CREATED,
                obj=manager,
                model_name="Аккаунт",
                object_repr=f"{manager.username} ({manager.get_role_display()})",
                ip_address=get_client_ip(request),
            )
            messages.success(
                request,
                f"Аккаунт создан. Логин: {manager.username} — сообщите его сотруднику, "
                f"пароль повторно посмотреть нельзя.",
            )
            return redirect("team_list")
    else:
        form = ManagerInviteForm()
    return render(request, "accounts/team_form.html", {"form": form, "is_new": True})


@login_required
@owner_required
def team_update(request, user_id):
    org = get_or_create_organization(request.user)
    member = get_object_or_404(User, pk=user_id, organization=org)
    if request.method == "POST":
        form = TeamMemberForm(data=request.POST, instance=member)
        if form.is_valid():
            password_changed = bool(form.cleaned_data.get("new_password1"))
            form.save()
            log_action(
                request.user,
                AuditLog.Action.UPDATED,
                obj=member,
                model_name="Аккаунт",
                object_repr=f"{member.username}" + (" (сброшен пароль)" if password_changed else ""),
                ip_address=get_client_ip(request),
            )
            messages.success(request, "Изменения сохранены.")
            return redirect("team_list")
    else:
        form = TeamMemberForm(instance=member)
    return render(
        request, "accounts/team_form.html", {"form": form, "is_new": False, "member": member}
    )


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            log_action(
                request.user,
                AuditLog.Action.UPDATED,
                obj=request.user,
                model_name="Профиль",
                object_repr=request.user.username,
                ip_address=get_client_ip(request),
            )
            messages.success(request, "Профиль обновлён.")
            return redirect("profile_edit")
    else:
        form = ProfileForm(instance=request.user)

    password_form = RussianPasswordChangeForm(user=request.user)
    return render(
        request, "accounts/profile.html", {"form": form, "password_form": password_form}
    )


@login_required
@require_POST
def profile_change_password(request):
    password_form = RussianPasswordChangeForm(user=request.user, data=request.POST)
    if password_form.is_valid():
        user = password_form.save()
        update_session_auth_hash(request, user)
        log_action(
            user,
            AuditLog.Action.UPDATED,
            obj=user,
            model_name="Профиль",
            object_repr=f"{user.username} (смена пароля)",
            ip_address=get_client_ip(request),
        )
        messages.success(request, "Пароль изменён.")
        return redirect("profile_edit")

    form = ProfileForm(instance=request.user)
    return render(
        request, "accounts/profile.html", {"form": form, "password_form": password_form}
    )
