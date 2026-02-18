"""Showcase log views: public, anonymous, read-only."""

from __future__ import annotations

from django.http import Http404
from django.views import View
from django.views.generic import DetailView, TemplateView

from flipfix.apps.core.mixins import InfiniteScrollMixin
from flipfix.apps.maintenance.models import LogEntry
from flipfix.apps.maintenance.views.log_entries import get_log_entry_queryset, get_log_list_context

from . import SHOWCASE_MAX_PAGE, ShowcaseEnabledMixin


class ShowcaseLogsView(ShowcaseEnabledMixin, TemplateView):
    """Public global list of all log entries."""

    template_name = "showcase/logs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_log_list_context(self.request))
        context["base_template"] = "base_showcase.html"

        return context


class ShowcaseLogEntriesView(ShowcaseEnabledMixin, InfiniteScrollMixin, View):
    """AJAX endpoint for infinite scrolling in the showcase log list."""

    item_template = "showcase/partials/log_global_card.html"

    def get_queryset(self):
        try:
            if int(self.request.GET.get(self.page_param, "1")) > SHOWCASE_MAX_PAGE:
                raise Http404
        except (TypeError, ValueError):
            pass
        search_query = self.request.GET.get("q", "").strip()
        return get_log_entry_queryset(search_query)


class ShowcaseLogView(ShowcaseEnabledMixin, DetailView):
    """Public read-only log entry detail."""

    model = LogEntry
    template_name = "showcase/log.html"
    context_object_name = "entry"

    def get_queryset(self):
        return LogEntry.objects.select_related("machine", "problem_report").prefetch_related(
            "media"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_template"] = "base_showcase.html"

        return context
