from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from accounts.decorators import role_required
from accounts.forms import LoginForm, RegisterForm, UserManagementForm
from accounts.models import User
from core.utils import log_activity


def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_redirect())
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_activity(user, 'Logged in', 'Authentication')
        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        return redirect(user.get_dashboard_redirect())
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.save()
        group_map = {
            User.ROLE_PROCUREMENT: 'Procurement Officer',
            User.ROLE_VENDOR: 'Vendor',
            User.ROLE_MANAGER: 'Manager',
        }
        group_name = group_map.get(user.role)
        if group_name:
            group = Group.objects.filter(name=group_name).first()
            if group:
                user.groups.add(group)
        log_activity(user, 'Registered new account', 'Authentication')
        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('accounts:login')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    log_activity(request.user, 'Logged out', 'Authentication')
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


class ForgotPasswordView(PasswordResetView):
    template_name = 'accounts/forgot_password.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class ForgotPasswordDoneView(PasswordResetDoneView):
    template_name = 'accounts/forgot_password_done.html'


class ForgotPasswordConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/forgot_password_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class ForgotPasswordCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/forgot_password_complete.html'


@login_required
@role_required(User.ROLE_ADMIN)
def manage_users(request):
    users = User.objects.all()
    q = request.GET.get('q', '')
    role = request.GET.get('role', '')
    if q:
        users = users.filter(username__icontains=q) | users.filter(email__icontains=q)
    if role:
        users = users.filter(role=role)
    return render(request, 'accounts/manage_users.html', {
        'users': users,
        'roles': User.ROLE_CHOICES,
        'q': q,
        'selected_role': role,
    })


@login_required
@role_required(User.ROLE_ADMIN)
def edit_user(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    form = UserManagementForm(request.POST or None, instance=user_obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_activity(request.user, f'Updated user {user_obj.username}', 'User Management')
        messages.success(request, 'User updated successfully.')
        return redirect('accounts:manage_users')
    return render(request, 'accounts/edit_user.html', {'form': form, 'user_obj': user_obj})


@login_required
@role_required(User.ROLE_ADMIN)
def toggle_user_status(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
    else:
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        status = 'activated' if user_obj.is_active else 'deactivated'
        log_activity(request.user, f'{status.title()} user {user_obj.username}', 'User Management')
        messages.success(request, f'User {status} successfully.')
    return redirect('accounts:manage_users')
