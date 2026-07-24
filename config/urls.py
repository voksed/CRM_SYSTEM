from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts.forms import ThrottledAuthenticationForm
from accounts.views import (
    analytics_dashboard,
    dashboard,
    profile_change_password,
    profile_edit,
    team_create,
    team_list,
    team_update,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('team/', team_list, name='team_list'),
    path('team/add/', team_create, name='team_create'),
    path('team/<int:user_id>/edit/', team_update, name='team_update'),
    path('profile/', profile_edit, name='profile_edit'),
    path('profile/password/', profile_change_password, name='profile_change_password'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='login.html', authentication_form=ThrottledAuthenticationForm
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('contacts/', include('contacts.urls')),
    path('deals/', include('deals.urls')),
    path('tasks/', include('tasks.urls')),
    path('billing/', include('billing.urls')),
    path('channels/', include('channels_app.urls')),
    path('automation/', include('automation.urls')),
    path('audit/', include('audit.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
