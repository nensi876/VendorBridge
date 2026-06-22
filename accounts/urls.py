from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='password_reset'),
    path('forgot-password/done/', views.ForgotPasswordDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.ForgotPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.ForgotPasswordCompleteView.as_view(), name='password_reset_complete'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/toggle/', views.toggle_user_status, name='toggle_user'),
]
