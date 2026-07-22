from django import forms

from accounts.models import User
from accounts.permissions import is_owner

from .models import Contact, Tag


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = [
            "full_name",
            "phone",
            "email",
            "source",
            "status",
            "tags",
            "responsible",
            "notes",
        ]
        widgets = {
            "tags": forms.SelectMultiple,
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organization = user.organization
        self.fields["tags"].queryset = Tag.objects.filter(organization=organization)
        self.fields["tags"].required = False

        if is_owner(user):
            self.fields["responsible"].queryset = User.objects.filter(organization=organization)
            self.fields["responsible"].required = False
            self.fields["responsible"].empty_label = "Не назначен"
        else:
            # менеджер не может переназначать контакты — ответственный всегда он сам
            del self.fields["responsible"]
