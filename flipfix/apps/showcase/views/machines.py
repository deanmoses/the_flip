"""Showcase machine views: public, anonymous, read-only."""

from __future__ import annotations

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, TemplateView

from flipfix.apps.catalog.models import MachineInstance
from flipfix.apps.catalog.views import get_machine_list_queryset, get_machine_list_stats
from flipfix.apps.core.feed import FEED_CONFIGS, FeedConfig, PageCursor, get_feed_page
from flipfix.apps.core.forms import SearchForm

from . import SHOWCASE_MAX_PAGE, ShowcaseEnabledMixin

# Feed configs available in showcase (excludes parts)
SHOWCASE_FEED_CONFIGS: dict[str, FeedConfig] = {
    key: config for key, config in FEED_CONFIGS.items() if key != "parts"
}


class ShowcaseMachinesView(ShowcaseEnabledMixin, ListView):
    """Public machine grid with location stats."""

    template_name = "showcase/machines.html"
    context_object_name = "machines"

    def get_queryset(self):
        return get_machine_list_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = get_machine_list_stats()
        context["base_template"] = "base_showcase.html"
        return context


class ShowcaseMachineView(ShowcaseEnabledMixin, TemplateView):
    """Public machine activity feed (problems + logs, no parts)."""

    template_name = "showcase/machine.html"

    def dispatch(self, request, *args, **kwargs):
        self.machine = get_object_or_404(MachineInstance, slug=kwargs["slug"])
        self.feed_filter_type = request.GET.get("f", "all")
        if self.feed_filter_type not in SHOWCASE_FEED_CONFIGS:
            self.feed_filter_type = "all"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed_config = SHOWCASE_FEED_CONFIGS[self.feed_filter_type]
        search_query = self.request.GET.get("q", "").strip()

        # Exclude parts from "all" — override entry_types
        entry_types = feed_config.entry_types or ("log", "problem_report")

        entries, has_next = get_feed_page(
            machine=self.machine,
            entry_types=entry_types,
            page_num=1,
            search_query=search_query or None,
        )

        # Tag entries with showcase templates
        for entry in entries:
            entry.showcase_template = _SHOWCASE_TEMPLATES.get(entry.entry_type, "")

        context.update(
            {
                "machine": self.machine,
                "entries": entries,
                "page_obj": PageCursor(has_next=has_next, page_num=1),
                "active_filter": self.feed_filter_type,
                "search_form": SearchForm(initial={"q": search_query}),
                "title_suffix": feed_config.title_suffix,
                "breadcrumb_label": feed_config.breadcrumb_label,
                "entry_types": entry_types,
                "empty_message": feed_config.empty_message,
                "search_empty_message": feed_config.search_empty_message,
                "base_template": "base_showcase.html",
            }
        )
        return context


class ShowcaseMachineEntriesView(ShowcaseEnabledMixin, View):
    """AJAX endpoint for infinite scroll of showcase machine feed."""

    def get(self, request, slug):
        try:
            machine = MachineInstance.objects.get(slug=slug)
        except MachineInstance.DoesNotExist:
            return JsonResponse({"error": "Machine not found"}, status=404)

        feed = request.GET.get("f", "all")
        if feed not in SHOWCASE_FEED_CONFIGS:
            feed = "all"
        feed_config = SHOWCASE_FEED_CONFIGS[feed]

        try:
            page_num = int(request.GET.get("page", 1))
        except (TypeError, ValueError):
            page_num = 1

        if page_num < 1 or page_num > SHOWCASE_MAX_PAGE:
            raise Http404

        search_query = request.GET.get("q", "").strip() or None
        entry_types = feed_config.entry_types or ("log", "problem_report")

        page_items, has_next = get_feed_page(
            machine=machine,
            entry_types=entry_types,
            page_num=page_num,
            search_query=search_query,
        )

        for entry in page_items:
            entry.showcase_template = _SHOWCASE_TEMPLATES.get(entry.entry_type, "")

        items_html = "".join(
            render_to_string("showcase/partials/feed_card.html", {"entry": entry}, request=request)
            for entry in page_items
        )

        return JsonResponse(
            {
                "items": items_html,
                "has_next": has_next,
                "next_page": page_num + 1 if has_next else None,
            }
        )


_SHOWCASE_TEMPLATES = {
    "log": "showcase/partials/log_machine_card.html",
    "problem_report": "showcase/partials/problem_card.html",
}
