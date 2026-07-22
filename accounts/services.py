from .models import Organization


def get_or_create_organization(user):
    """Первый вход владельца автоматически создаёт его рабочее пространство
    вместе с воронкой продаж по умолчанию, чтобы не городить отдельный флоу
    регистрации организации для MVP."""
    if user.organization_id:
        return user.organization

    from deals.services import create_default_pipeline

    org = Organization.objects.create(name=f"Кабинет {user.username}", owner=user)
    user.organization = org
    user.save(update_fields=["organization"])
    create_default_pipeline(org)
    return org
