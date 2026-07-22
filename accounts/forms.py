from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import User

LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60

USER_LABELS = {
    "username": "Логин",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "email": "Email",
    "phone": "Телефон",
}


class ManagerInviteForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Повторите пароль")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone"]
        labels = USER_LABELS

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают.")
        if password1:
            password_validation.validate_password(password1, self.instance)
        return password2

    def save(self, organization, commit=True):
        user = super().save(commit=False)
        user.organization = organization
        user.role = User.Role.MANAGER
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
        labels = USER_LABELS


class TeamMemberForm(forms.ModelForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Новый пароль",
        help_text="Оставьте пустым, чтобы не менять",
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput, required=False, label="Повторите новый пароль"
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role"]
        labels = USER_LABELS

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 or password2:
            if password1 != password2:
                raise ValidationError("Пароли не совпадают.")
            password_validation.validate_password(password1, self.instance)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password1")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user


class RussianPasswordChangeForm(PasswordChangeForm):
    """PasswordChangeForm с русскими подписями полей — билтин Django-класс
    не всегда переведён без настроенного LocaleMiddleware."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Текущий пароль"
        self.fields["new_password1"].label = "Новый пароль"
        self.fields["new_password2"].label = "Повторите новый пароль"


class ThrottledAuthenticationForm(AuthenticationForm):
    """Блокирует вход по логину после серии неудачных попыток —
    защита от подбора пароля перебором."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["password"].label = "Пароль"

    def clean(self):
        username = self.cleaned_data.get("username", "")
        cache_key = f"login_attempts:{username.lower()}"
        attempts = cache.get(cache_key, 0)

        if attempts >= LOGIN_MAX_ATTEMPTS:
            raise ValidationError(
                "Слишком много неудачных попыток входа. "
                "Попробуйте снова через 15 минут.",
                code="too_many_attempts",
            )

        try:
            cleaned_data = super().clean()
        except ValidationError:
            cache.set(cache_key, attempts + 1, LOGIN_LOCKOUT_SECONDS)
            raise
        cache.delete(cache_key)
        return cleaned_data
