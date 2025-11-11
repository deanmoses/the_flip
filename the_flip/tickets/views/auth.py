"""Authentication-related views."""

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


def home(request):
    """Redirect to the maintainer task list."""

    return redirect('task_list')


class CustomLoginView(LoginView):
    """Custom login view with the tickets template."""

    template_name = 'tickets/login.html'
    redirect_authenticated_user = True

