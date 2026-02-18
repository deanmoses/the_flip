"""Parts domain display: settable pills and meta formatters."""

from django import template
from django.utils.html import format_html

from flipfix.apps.core.templatetags.ui_tags import _settable_pill_context, smart_date

register = template.Library()


@register.inclusion_tag("components/settable_pill.html", takes_context=True)
def settable_part_request_status_pill(context, part_request):
    """Render a settable status dropdown pill for a part request.

    Usage:
        {% settable_part_request_status_pill part_request %}
    """
    ctx = _settable_pill_context(
        field="status",
        action="update_status",
        current_value=part_request.status,
        display_value=part_request.get_status_display(),
        items=[{"value": v, "label": label} for v, label in type(part_request).Status.choices],
    )
    ctx["user"] = context["user"]
    return ctx


@register.simple_tag(takes_context=True)
def part_request_meta(context, part_request):
    """Render requester name (if present) followed by timestamp (emphasized).

    Example: "Alice · <strong><time ...>...</time></strong>"
    If no requester, or if the user is unauthenticated, only render the timestamp.
    """
    if not part_request:
        return ""

    ts = smart_date(getattr(part_request, "occurred_at", None))

    if not context["user"].is_authenticated:
        return format_html("<strong>{}</strong>", ts)

    name = (getattr(part_request, "requester_display", "") or "").strip()

    if name:
        return format_html("{} · <strong>{}</strong>", name, ts)
    return format_html("<strong>{}</strong>", ts)


@register.simple_tag(takes_context=True)
def part_update_meta(context, update):
    """Render poster name (if present) followed by timestamp (emphasized).

    Example: "Alice · <strong><time ...>...</time></strong>"
    If no poster, or if the user is unauthenticated, only render the timestamp.
    """
    if not update:
        return ""

    ts = smart_date(getattr(update, "occurred_at", None))

    if not context["user"].is_authenticated:
        return format_html("<strong>{}</strong>", ts)

    name = (getattr(update, "poster_display", "") or "").strip()

    if name:
        return format_html("{} · <strong>{}</strong>", name, ts)
    return format_html("<strong>{}</strong>", ts)
