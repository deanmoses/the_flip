from django.http import JsonResponse
from django.views.generic import TemplateView

from the_flip.apps.core.health import check_db_and_orm


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if current user is a shared account
        is_shared_account = False
        if self.request.user.is_authenticated and hasattr(self.request.user, "maintainer"):
            is_shared_account = self.request.user.maintainer.is_shared_account
        context["is_shared_account"] = is_shared_account
        return context


def healthz(request):
    """Public health check endpoint for Railway."""
    try:
        details = check_db_and_orm()
    except Exception as exc:  # noqa: BLE001
        resp = JsonResponse({"status": "error", "error": str(exc)})
        resp.status_code = 503
        resp["Cache-Control"] = "no-store"
        return resp

    resp = JsonResponse({"status": "ok", "checks": details})
    resp["Cache-Control"] = "no-store"
    return resp
