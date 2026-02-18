"""Showcase problem views: public, anonymous, read-only."""

from __future__ import annotations

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView, TemplateView

from flipfix.apps.core.mixins import InfiniteScrollMixin
from flipfix.apps.maintenance.models import ProblemReport
from flipfix.apps.maintenance.views.problem_reports import (
    get_problem_board_context,
    get_problem_detail_context,
    get_problem_log_entry_queryset,
)

from . import SHOWCASE_MAX_PAGE, ShowcaseEnabledMixin


class ShowcaseProblemsView(ShowcaseEnabledMixin, TemplateView):
    """Public column board of open problem reports, grouped by location."""

    template_name = "showcase/problems.html"
    max_results_per_column = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_problem_board_context(self.request, self.max_results_per_column))
        context["card_template"] = "showcase/partials/problem_column_card.html"
        context["base_template"] = "base_showcase.html"

        return context


class ShowcaseProblemView(ShowcaseEnabledMixin, DetailView):
    """Public read-only problem report detail."""

    model = ProblemReport
    template_name = "showcase/problem.html"
    context_object_name = "report"

    def get_queryset(self):
        return ProblemReport.objects.select_related("machine")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_problem_detail_context(self.object, self.request))
        context["base_template"] = "base_showcase.html"

        return context


class ShowcaseProblemEntriesView(ShowcaseEnabledMixin, InfiniteScrollMixin, View):
    """AJAX endpoint for infinite scrolling log entries on a showcase problem detail."""

    item_template = "showcase/partials/log_problem_card.html"

    def get_queryset(self):
        try:
            if int(self.request.GET.get(self.page_param, "1")) > SHOWCASE_MAX_PAGE:
                raise Http404
        except (TypeError, ValueError):
            pass
        problem_report = get_object_or_404(ProblemReport, pk=self.kwargs["pk"])
        return get_problem_log_entry_queryset(problem_report, self.request.GET.get("q", ""))
