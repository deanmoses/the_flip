"""Global activity feed: paginated activity entries across all machines.

This module provides a single entry point for fetching global activity feeds,
combining logs, problem reports, and parts entries across all machines.
"""

from __future__ import annotations

from django.conf import settings
from django.db.models import Prefetch

from the_flip.apps.maintenance.models import LogEntry, ProblemReport
from the_flip.apps.parts.models import PartRequest, PartRequestUpdate

# Type alias for feed entries (all have occurred_at and ENTRY_TYPE attributes)
FeedEntry = LogEntry | ProblemReport | PartRequest | PartRequestUpdate


class PageCursor:
    """Pagination cursor for templates that expect page_obj interface.

    Used when merging multiple querysets where Django's Paginator can't be used.
    """

    def __init__(self, has_next: bool, page_num: int = 1):
        self._has_next = has_next
        self._page_num = page_num

    def has_next(self) -> bool:
        return self._has_next

    def next_page_number(self) -> int:
        return self._page_num + 1


def get_global_feed_page(
    page_num: int,
    page_size: int = settings.LIST_PAGE_SIZE,
    search_query: str | None = None,
) -> tuple[list[FeedEntry], bool]:
    """Get a paginated page of global activity entries across all machines.

    Uses merge-sort style pagination: fetches just enough from each table
    to construct the requested page.

    Args:
        page_num: Page number (1-indexed).
        page_size: Number of items per page (default: settings.LIST_PAGE_SIZE).
        search_query: Optional search string to filter results.

    Returns:
        Tuple of (page_items, has_next) where page_items is a list of entries
        and has_next indicates if more pages exist.
    """
    offset = (page_num - 1) * page_size
    # Fetch one extra to detect if more pages exist (countless pagination pattern)
    fetch_limit = offset + page_size + 1

    all_entries: list[FeedEntry] = []

    all_entries.extend(_get_global_log_entries(search_query, fetch_limit))
    all_entries.extend(_get_global_problem_reports(search_query, fetch_limit))
    all_entries.extend(_get_global_part_requests(search_query, fetch_limit))
    all_entries.extend(_get_global_part_request_updates(search_query, fetch_limit))

    # Sort by occurred_at descending (all entry types)
    combined = sorted(
        all_entries,
        key=lambda x: x.occurred_at,
        reverse=True,
    )

    # Slice to requested page
    page_items = combined[offset : offset + page_size]
    has_next = len(combined) > offset + page_size

    return page_items, has_next


def _get_global_log_entries(search_query: str | None, limit: int) -> list[LogEntry]:
    """Get global log entries with optional search filter."""
    queryset = LogEntry.objects.select_related(
        "machine", "machine__model", "problem_report"
    ).prefetch_related("maintainers__user", "media")

    if search_query:
        queryset = queryset.search(search_query)

    queryset = queryset.order_by("-occurred_at")
    return list(queryset[:limit])


def _get_global_problem_reports(search_query: str | None, limit: int) -> list[ProblemReport]:
    """Get global problem reports with optional search filter."""
    latest_log_prefetch = Prefetch(
        "log_entries",
        queryset=LogEntry.objects.order_by("-occurred_at"),
        to_attr="prefetched_log_entries",
    )
    queryset = ProblemReport.objects.select_related(
        "machine", "machine__model", "reported_by_user"
    ).prefetch_related(latest_log_prefetch, "media")

    if search_query:
        queryset = queryset.search(search_query)

    queryset = queryset.order_by("-occurred_at")
    return list(queryset[:limit])


def _get_global_part_requests(search_query: str | None, limit: int) -> list[PartRequest]:
    """Get global part requests with optional search filter."""
    latest_update_prefetch = Prefetch(
        "updates",
        queryset=PartRequestUpdate.objects.order_by("-occurred_at"),
        to_attr="prefetched_updates",
    )
    queryset = PartRequest.objects.select_related(
        "machine", "machine__model", "requested_by__user"
    ).prefetch_related("media", latest_update_prefetch)

    if search_query:
        queryset = queryset.search(search_query)

    queryset = queryset.order_by("-occurred_at")
    return list(queryset[:limit])


def _get_global_part_request_updates(
    search_query: str | None, limit: int
) -> list[PartRequestUpdate]:
    """Get global part request updates with optional search filter."""
    queryset = PartRequestUpdate.objects.select_related(
        "posted_by__user", "part_request", "part_request__machine"
    ).prefetch_related("media")

    if search_query:
        queryset = queryset.search(search_query)

    queryset = queryset.order_by("-occurred_at")
    return list(queryset[:limit])
