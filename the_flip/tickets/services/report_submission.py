"""Utilities that support visitor-facing problem report submission."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.utils import timezone


def get_request_ip(request) -> str | None:
    """Best-effort extraction of the originating client IP."""

    header_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if header_ip:
        candidate = header_ip.split(',')[0].strip()
    else:
        candidate = request.META.get('REMOTE_ADDR', '')

    if not candidate:
        return None

    try:
        validate_ipv46_address(candidate)
    except ValidationError:
        return None
    return candidate


def report_submission_rate_limit_exceeded(ip_address: str | None) -> bool:
    """Return True when a client has exceeded the problem report submission rate."""

    if not ip_address:
        return False

    max_reports = getattr(settings, 'REPORT_SUBMISSION_RATE_LIMIT_MAX', 5)
    window_seconds = getattr(settings, 'REPORT_SUBMISSION_RATE_LIMIT_WINDOW_SECONDS', 10 * 60)

    if max_reports <= 0 or window_seconds <= 0:
        return False

    cache_key = f'report-rate:{ip_address}'
    now = timezone.now()
    entry = cache.get(cache_key)

    if entry:
        reset_at = entry.get('reset_at')
        if not reset_at or reset_at <= now:
            entry = None
        else:
            count = entry.get('count', 0)
            if count >= max_reports:
                return True
            entry['count'] = count + 1
            remaining = max(int((reset_at - now).total_seconds()), 0)
            cache.set(cache_key, entry, timeout=remaining)
            return False

    reset_at = now + timedelta(seconds=window_seconds)
    cache.set(cache_key, {'count': 1, 'reset_at': reset_at}, timeout=window_seconds)
    return False

