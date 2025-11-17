from django.views.generic import DetailView, ListView

from the_flip.apps.catalog.models import MachineInstance
from the_flip.apps.maintenance.forms import ProblemReportForm
from the_flip.apps.maintenance.models import LogEntry, ProblemReport


class PublicMachineListView(ListView):
    template_name = "catalog/machine_list_public.html"
    context_object_name = "machines"
    queryset = MachineInstance.objects.visible().order_by("model__year")


class MachineListView(PublicMachineListView):
    template_name = "catalog/machine_list.html"


class PublicMachineDetailView(DetailView):
    template_name = "catalog/machine_detail.html"
    queryset = MachineInstance.objects.visible()
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        machine = self.object
        context["problem_reports"] = ProblemReport.objects.filter(machine=machine).select_related("reported_by_user")
        context["log_entries"] = (
            LogEntry.objects.filter(machine=machine)
            .select_related("problem_report")
            .prefetch_related("maintainers", "media")
        )
        context["problem_report_form"] = ProblemReportForm()
        return context


class MachineDetailView(PublicMachineDetailView):
    """Maintainer-facing detail page; customize as needed."""

    template_name = "catalog/maintainer_machine_detail.html"
