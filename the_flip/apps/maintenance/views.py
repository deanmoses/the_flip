from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView, FormView

from the_flip.apps.catalog.models import MachineInstance
from the_flip.apps.maintenance.forms import ProblemReportForm
from the_flip.apps.maintenance.models import LogEntry, ProblemReport


class MaintenanceIndexView(TemplateView):
    template_name = "maintenance/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_reports"] = ProblemReport.objects.open().select_related("machine").order_by("-created_at")
        context["recent_logs"] = LogEntry.objects.select_related("machine").prefetch_related("maintainers")[:10]
        return context


class ProblemReportListView(ListView):
    template_name = "maintenance/problem_report_list.html"
    context_object_name = "reports"
    queryset = ProblemReport.objects.select_related("machine").order_by("-created_at")


class ProblemReportCreateView(FormView):
    template_name = "maintenance/problem_report_form.html"
    form_class = ProblemReportForm

    def dispatch(self, request, *args, **kwargs):
        self.machine = get_object_or_404(MachineInstance, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["machine"] = self.machine
        return context

    def form_valid(self, form):
        report = form.save(commit=False)
        report.machine = self.machine
        report.ip_address = self.request.META.get("REMOTE_ADDR")
        report.save()
        messages.success(self.request, "Thanks! The maintenance team has been notified.")
        return redirect(self.machine.get_absolute_url())
