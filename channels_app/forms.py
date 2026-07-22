from django import forms

from .models import Activity, TelegramAccount


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
        fields = ["bot_token", "is_active"]
        labels = {"is_active": "Бот активен"}
