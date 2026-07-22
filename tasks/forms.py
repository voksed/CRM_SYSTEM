from django import forms

from accounts.models import User
from accounts.permissions import is_owner, scope_to_owner_field
from contacts.models import Contact
from deals.models import Deal

from .models import Task


class TaskForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
        label="Срок выполнения",
    )

    class Meta:
        model = Task
        fields = ["title", "task_type", "contact", "deal", "assigned_to", "due_at"]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organization = user.organization
        contacts = Contact.objects.filter(organization=organization)
        self.fields["contact"].queryset = scope_to_owner_field(contacts, user)
        self.fields["contact"].required = False
        self.fields["contact"].empty_label = "Без привязки к контакту"

        deals = Deal.objects.filter(organization=organization)
        self.fields["deal"].queryset = scope_to_owner_field(deals, user)
        self.fields["deal"].required = False
        self.fields["deal"].empty_label = "Без привязки к сделке"

        if is_owner(user):
            self.fields["assigned_to"].queryset = User.objects.filter(organization=organization)
            self.fields["assigned_to"].empty_label = None
        else:
            # менеджер ставит задачи только себе
            del self.fields["assigned_to"]
