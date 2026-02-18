"""Showcase-specific template tags: anonymized meta, linkless markdown, nav."""

from __future__ import annotations

from django import template
from django.utils.html import format_html

from flipfix.apps.core.templatetags.ui_tags import smart_date

register = template.Library()


# ---- Nav --------------------------------------------------------------------

_SHOWCASE_NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    # (label, url_name, active_contains)
    ("Machines", "showcase:machines", "machine"),
    ("Problems", "showcase:problems", "problem"),
    ("Logs", "showcase:logs", "log"),
)


@register.inclusion_tag("showcase/components/nav.html", takes_context=True)
def showcase_nav(context: dict) -> dict:
    """Render the showcase navigation bar with active-state detection.

    Uses ``request.resolver_match.url_name`` substring matching, same
    approach as the maintainer nav in ``nav_tags``.

    Usage::

        {% load showcase_tags %}
        {% showcase_nav %}
    """
    request = context.get("request")
    url_name = ""
    if request and request.resolver_match:
        url_name = request.resolver_match.url_name or ""

    items = [
        {
            "label": label,
            "url_name": nav_url_name,
            "is_active": active_contains in url_name,
        }
        for label, nav_url_name, active_contains in _SHOWCASE_NAV_ITEMS
    ]
    return {"nav_items": items}


# ---- Filters ----------------------------------------------------------------


@register.filter
def log_entry_meta(entry):
    """Render log entry timestamp without maintainer names.

    Showcase equivalent of maintenance_tags.log_entry_meta. Returns only
    the emphasized timestamp — no names, no PII.
    """
    if not entry:
        return ""
    ts = smart_date(getattr(entry, "occurred_at", None))
    return format_html("<strong>{}</strong>", ts)


@register.filter
def problem_report_meta(report):
    """Render problem report timestamp without reporter name.

    Showcase equivalent of maintenance_tags.problem_report_meta. Returns
    only the emphasized timestamp — no names, no PII.
    """
    if not report:
        return ""
    ts = smart_date(getattr(report, "occurred_at", None))
    return format_html("<strong>{}</strong>", ts)


@register.filter
def render_markdown_showcase(text):
    """Render markdown with [[type:ref]] links as plain text labels.

    Uses the standard markdown pipeline but disables live links so internal
    URLs (which require authentication) are not exposed to public visitors.
    """
    from flipfix.apps.core.markdown import render_markdown_html

    return render_markdown_html(text, live_links=False)
