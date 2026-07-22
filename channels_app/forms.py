from django import forms

from .models import Activity


class LogActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["type", "channel", "direction", "text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = Activity.Type.choices
        self.fields["direction"].choices = [("", "—")] + list(Activity.Direction.choices)


class SendMessageForm(forms.Form):
    channel = forms.ChoiceField(
        choices=Activity.Channel.choices,
        initial=Activity.Channel.TELEGRAM,
        label="Канал",
    )
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Текст")
