from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('core:dashboard')
        return wrapper
    return decorator
