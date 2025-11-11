"""Custom decorators for the tickets app."""

from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def maintainer_required(view_func=None, *, redirect_url_name: str = 'task_list', message: str | None = None):
    """Ensure the current user is staff or linked to a maintainer profile."""

    def decorator(func):
        @wraps(func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated and (user.is_staff or hasattr(user, 'maintainer')):
                return func(request, *args, **kwargs)

            messages.error(request, message or 'You do not have permission to access this page.')
            return redirect(redirect_url_name)

        return _wrapped

    if view_func is None:
        return decorator
    return decorator(view_func)

