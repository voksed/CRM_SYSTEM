from django import forms

from .models import Activity, LeadQuestion, TelegramAccount


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
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Сообщение в Telegram")


class TelegramSettingsForm(forms.ModelForm):
    bot_token = forms.CharField(
        label="Токен бота",
        help_text="Получить у @BotFather в Telegram",
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    class Meta:
        model = TelegramAccount
        fields = [
            "title",
            "bot_token",
            "is_active",
            "welcome_text",
            "help_text_message",
            "operator_text",
            "collect_lead",
            "lead_done_text",
        ]
        widgets = {
            "welcome_text": forms.Textarea(attrs={"rows": 2}),
            "help_text_message": forms.Textarea(attrs={"rows": 2}),
            "operator_text": forms.Textarea(attrs={"rows": 2}),
            "lead_done_text": forms.Textarea(attrs={"rows": 2}),
        }


class LeadQuestionForm(forms.ModelForm):
    class Meta:
        model = LeadQuestion
        fields = ["order", "text", "target"]
        widgets = {
            "order": forms.NumberInput(attrs={"style": "width:70px"}),
            "text": forms.TextInput(attrs={"placeholder": "Например: Как вас зовут?"}),
        }


LeadQuestionFormSet = forms.inlineformset_factory(
    TelegramAccount,
    LeadQuestion,
    form=LeadQuestionForm,
    extra=3,
    can_delete=True,
)
