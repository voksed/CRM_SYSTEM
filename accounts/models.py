from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """Тенант: компания, использующая CRM."""

    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="owned_organizations",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Владелец"
        MANAGER = "manager", "Менеджер"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.OWNER, verbose_name="Роль"
    )
    phone = models.CharField(max_length=32, blank=True, verbose_name="Телефон")

    def __str__(self):
        return self.get_full_name() or self.username
