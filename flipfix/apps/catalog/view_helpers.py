"""View helpers for catalog models."""

from flipfix.apps.catalog.models import MachineInstance


def resolve_selected_machine(request, machine):
    """Resolve the selected machine from POST data or a URL-derived instance."""
    if machine:
        return machine
    if request.method == "POST":
        slug = request.POST.get("machine_slug", "")
        if slug:
            return MachineInstance.objects.filter(slug=slug).first()
    return None
