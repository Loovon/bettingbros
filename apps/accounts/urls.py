from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('responsible-gambling/', views.responsible_gambling_view, name='responsible_gambling'),
    path(
        'password/change/',
        auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'),
        name='password_change',
    ),
    path(
        'password/change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done',
    ),
]
