from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import is_owner, scope_claimable, scope_to_owner_field
from accounts.services import get_or_create_organization
from audit.models import AuditLog
from audit.services import get_client_ip, log_action
from channels_app.forms import LogActivityForm, SendMessageForm
from channels_app.models import Activity
from channels_app.services import send_message

from .forms import ContactForm
from .models import Contact


@login_required
def contact_list(request):
    org = get_or_create_organization(request.user)
    contacts = Contact.objects.filter(organization=org).select_related("responsible")
    contacts = scope_claimable(contacts, request.user)

    status = request.GET.get("status")
    if status:
        contacts = contacts.filter(status=status)

    query = request.GET.get("q", "").strip()
    if query:
        contacts = contacts.filter(
            Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )

    context = {
        "contacts": contacts,
        "statuses": Contact.Status.choices,
        "active_status": status,
        "query": query,
    }
    return render(request, "contacts/list.html", context)


@login_required
def contact_create(request):
    org = get_or_create_organization(request.user)
    if request.method == "POST":
        form = ContactForm(request.user, data=request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.organization = org
            if not is_owner(request.user):
                contact.responsible = request.user
            contact.save()
            form.save_m2m()
            log_action(
                request.user,
                AuditLog.Action.CREATED,
                obj=contact,
                model_name="Контакт",
                ip_address=get_client_ip(request),
            )
            return redirect("contact_detail", contact_id=contact.id)
    else:
        form = ContactForm(request.user)
    return render(request, "contacts/form.html", {"form": form, "is_new": True})


@login_required
def contact_update(request, contact_id):
    org = get_or_create_organization(request.user)
    contacts = scope_to_owner_field(Contact.objects.filter(organization=org), request.user)
    contact = get_object_or_404(contacts, pk=contact_id)
    if request.method == "POST":
        form = ContactForm(request.user, data=request.POST, instance=contact)
        if form.is_valid():
            form.save()
            log_action(
                request.user,
                AuditLog.Action.UPDATED,
                obj=contact,
                model_name="Контакт",
                ip_address=get_client_ip(request),
            )
            return redirect("contact_detail", contact_id=contact.id)
    else:
        form = ContactForm(request.user, instance=contact)
    return render(request, "contacts/form.html", {"form": form, "is_new": False, "contact": contact})


@login_required
@require_POST
def contact_delete(request, contact_id):
    org = get_or_create_organization(request.user)
    contacts = scope_to_owner_field(Contact.objects.filter(organization=org), request.user)
    contact = get_object_or_404(contacts, pk=contact_id)
    log_action(
        request.user,
        AuditLog.Action.DELETED,
        obj=contact,
        model_name="Контакт",
        ip_address=get_client_ip(request),
    )
    contact.delete()
    return redirect("contact_list")


@login_required
def contact_detail(request, contact_id):
    org = get_or_create_organization(request.user)
    contacts = scope_claimable(Contact.objects.filter(organization=org), request.user)
    contact = get_object_or_404(contacts, pk=contact_id)
    can_claim = contact.responsible_id is None and not is_owner(request.user)

    chat_messages = contact.activities.filter(channel=Activity.Channel.TELEGRAM).order_by(
        "created_at"
    )
    activity_log = contact.activities.exclude(channel=Activity.Channel.TELEGRAM).select_related(
        "created_by"
    )
    deals = contact.deals.select_related("stage")
    tasks = contact.tasks.filter(is_done=False).order_by("due_at")

    log_form = LogActivityForm()
    send_form = SendMessageForm()

    context = {
        "contact": contact,
        "can_claim": can_claim,
        "chat_messages": chat_messages,
        "activity_log": activity_log,
        "deals": deals,
        "tasks": tasks,
        "log_form": log_form,
        "send_form": send_form,
    }
    return render(request, "contacts/detail.html", context)


@login_required
@require_POST
def contact_claim(request, contact_id):
    org = get_or_create_organization(request.user)
    contact = get_object_or_404(
        Contact, pk=contact_id, organization=org, responsible__isnull=True
    )
    contact.responsible = request.user
    contact.save(update_fields=["responsible"])
    log_action(
        request.user,
        AuditLog.Action.UPDATED,
        obj=contact,
        model_name="Контакт",
        object_repr=f"{contact.full_name} (взял в работу)",
        ip_address=get_client_ip(request),
    )
    return redirect("contact_detail", contact_id=contact.id)


@login_required
@require_POST
def contact_log_activity(request, contact_id):
    org = get_or_create_organization(request.user)
    contacts = scope_to_owner_field(Contact.objects.filter(organization=org), request.user)
    contact = get_object_or_404(contacts, pk=contact_id)
    form = LogActivityForm(data=request.POST)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.organization = org
        activity.contact = contact
        activity.created_by = request.user
        activity.save()
    return redirect("contact_detail", contact_id=contact.id)


@login_required
@require_POST
def contact_send_message(request, contact_id):
    org = get_or_create_organization(request.user)
    contacts = scope_to_owner_field(Contact.objects.filter(organization=org), request.user)
    contact = get_object_or_404(contacts, pk=contact_id)
    form = SendMessageForm(data=request.POST)
    if form.is_valid():
        send_message(
            org, contact, Activity.Channel.TELEGRAM, form.cleaned_data["text"], request.user
        )
    return redirect("contact_detail", contact_id=contact.id)


@login_required
def contact_telegram_messages_json(request, contact_id):
    org = get_or_create_organization(request.user)
    contacts = scope_to_owner_field(Contact.objects.filter(organization=org), request.user)
    contact = get_object_or_404(contacts, pk=contact_id)

    messages = contact.activities.filter(channel=Activity.Channel.TELEGRAM).order_by("created_at")
    after_id = request.GET.get("after_id")
    if after_id:
        messages = messages.filter(id__gt=after_id)

    return JsonResponse({
        "messages": [
            {
                "id": message.id,
                "direction": message.direction,
                "text": message.text,
                "created_at": message.created_at.strftime("%d.%m %H:%M"),
                "failed": message.delivery_failed,
                "error": message.delivery_error,
            }
            for message in messages
        ]
    })
