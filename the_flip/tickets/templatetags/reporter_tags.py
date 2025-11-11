from django import template
from tickets.models import Maintainer

register = template.Library()


@register.simple_tag(takes_context=True)
def reporter_display(context, report):
    """
    Display reporter information based on user authentication status.

    For public (unauthenticated) view:
        - Shows reporter name if provided
        - Otherwise shows empty string

    For authenticated view: returns first available from priority list:
        1. Reporter user's short name (if they're a maintainer) or full name/username
        2. Reporter name (from anonymous submission)
        3. Reporter email or phone
        4. Empty string
    """
    request = context.get('request')
    user = context.get('user')

    # For authenticated users, show reporter info with full priority fallback
    if user and user.is_authenticated:
        if report.reported_by_user:
            # If reported by a logged-in user who is a maintainer, use short_name
            try:
                return report.reported_by_user.maintainer.short_name
            except:
                # Not a maintainer, use full name or username
                return report.reported_by_user.get_full_name() or report.reported_by_user.username

        # For anonymous reports, use priority fallback
        if report.reported_by_name:
            return report.reported_by_name
        if report.reported_by_contact:
            return report.reported_by_contact

        return ""

    # For unauthenticated users, only show name if provided
    if report.reported_by_name:
        return report.reported_by_name

    return ""


@register.filter
def creator_display(task):
    """
    Display creator/reporter name for a task.
    If the task was created by a maintainer, use their short_name.
    Otherwise, return the reported_by_name or "Anonymous".
    """
    if task.reported_by_user:
        # If created by a logged-in user who is a maintainer, use short_name
        try:
            return task.reported_by_user.maintainer.short_name
        except:
            # Not a maintainer, use full name or username
            return task.reported_by_user.get_full_name() or task.reported_by_user.username

    # Fallback to reported_by_name or "Anonymous"
    return task.reported_by_name if task.reported_by_name else "Anonymous"
