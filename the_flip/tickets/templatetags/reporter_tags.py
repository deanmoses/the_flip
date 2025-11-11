from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def reporter_display(context, report):
    """
    Display reporter information based on user authentication status.

    For public (unauthenticated) view:
        - Shows reporter name if provided
        - Otherwise shows empty string

    For authenticated view: returns first available from priority list:
        1. Reporter user's full name or username (if reported by authenticated user)
        2. Reporter name (from anonymous submission)
        3. Reporter email
        4. Reporter phone
        5. User agent
        6. Empty string
    """
    request = context.get('request')
    user = context.get('user')

    # For authenticated users, show reporter info with full priority fallback
    if user and user.is_authenticated:
        if report.reported_by_user:
            # If reported by a logged-in user, show their name
            return report.reported_by_user.get_full_name() or report.reported_by_user.username

        # For anonymous reports, use priority fallback
        if report.reported_by_name:
            return report.reported_by_name
        if report.reported_by_contact:
            return report.reported_by_contact
        if report.device_info:
            return report.device_info

        return ""

    # For unauthenticated users, only show name if provided
    if report.reported_by_name:
        return report.reported_by_name

    return ""
