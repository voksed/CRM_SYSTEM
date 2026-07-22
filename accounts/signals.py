from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from audit.models import AuditLog
from audit.services import get_client_ip, log_action


@receiver(user_logged_in)
def on_login_success(sender, request, user, **kwargs):
    log_action(
        user,
        AuditLog.Action.LOGIN_SUCCESS,
        object_repr="Вход в систему",
        ip_address=get_client_ip(request),
    )


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    username = credentials.get("username", "") if credentials else ""
    log_action(
        None,
        AuditLog.Action.LOGIN_FAILED,
        object_repr="Неудачная попытка входа",
        actor_username=username,
        ip_address=get_client_ip(request),
    )
