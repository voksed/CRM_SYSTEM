from django import forms

from accounts.models import User
from accounts.permissions import is_owner, scope_to_owner_field
from contacts.models import Contact

from .models import Deal, Stage


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ["title", "contact", "stage", "amount", "responsible"]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organization = user.organization
        contacts = Contact.objects.filter(organization=organization)
        self.fields["contact"].queryset = scope_to_owner_field(contacts, user)
        self.fields["contact"].empty_label = None
        self.fields["stage"].queryset = Stage.objects.filter(pipeline__organization=organization)
        self.fields["stage"].empty_label = None

        if is_owner(user):
            self.fields["responsible"].queryset = User.objects.filter(organization=organization)
            self.fields["responsible"].required = False
            self.fields["responsible"].empty_label = "Не назначен"
        else:
            del self.fields["responsible"]
