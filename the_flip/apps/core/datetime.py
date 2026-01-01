"""Datetime utilities for handling browser timezone conversion."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django import forms
from django.http import HttpRequest
from django.utils import timezone


def apply_browser_timezone(dt, request: HttpRequest):
    """
    Reinterpret a datetime in the browser's timezone.

    HTML datetime-local inputs send values without timezone info. Django parses
    these as naive datetimes and makes them aware using the server's TIME_ZONE
    setting (UTC). But the user entered the time in their browser's local timezone.

    This function reads the browser_timezone hidden field (set by JS to the
    browser's IANA timezone like "America/Los_Angeles") and reinterprets the
    datetime in that timezone, correctly handling DST.

    Args:
        dt: A datetime value from a form's cleaned_data
        request: The HTTP request containing POST data with browser_timezone

    Returns:
        The datetime with correct timezone, or the original if conversion fails
    """
    if not dt:
        return dt

    tz_name = request.POST.get("browser_timezone", "")
    if not tz_name:
        return dt

    try:
        browser_tz = ZoneInfo(tz_name)
        # Strip existing timezone and apply browser's timezone
        naive_dt = dt.replace(tzinfo=None)
        return naive_dt.replace(tzinfo=browser_tz)
    except (KeyError, ValueError):
        # Invalid timezone name
        return dt


def parse_datetime_with_browser_timezone(value: str, request: HttpRequest):
    """
    Parse a datetime-local string and apply browser timezone.

    For use with raw POST data (not form cleaned_data). Parses the string,
    then applies browser timezone correction.

    Args:
        value: A datetime string like "2024-12-31T14:30"
        request: The HTTP request containing POST data with browser_timezone

    Returns:
        A timezone-aware datetime, or None if parsing fails
    """
    if not value:
        return None

    try:
        # Parse as naive datetime, then apply browser timezone
        naive_dt = datetime.strptime(value, "%Y-%m-%dT%H:%M")
        return apply_browser_timezone(naive_dt, request)
    except (ValueError, TypeError):
        return None


def validate_not_future(dt, form: forms.Form, field_name: str = "occurred_at") -> bool:
    """
    Add a form error if the datetime is in the future.

    Call this after apply_browser_timezone() to validate user-entered dates.
    Form validation runs before timezone conversion, so this check must happen
    in the view's form_valid() method.

    Args:
        dt: A timezone-aware datetime to validate
        form: The form to add errors to
        field_name: The field name for the error (default: "occurred_at")

    Returns:
        True if valid (not in the future), False if invalid (error added to form)
    """
    if dt and dt > timezone.now():
        form.add_error(field_name, "Date cannot be in the future.")
        return False
    return True
