"""Showcase views: public, anonymous, read-only mirrors of operational data."""

from constance import config
from django.http import Http404
from django.utils.cache import patch_cache_control

# Maximum page number for infinite scroll endpoints (abuse prevention)
SHOWCASE_MAX_PAGE = 100


class ShowcaseEnabledMixin:
    """Return 404 when the showcase is disabled via constance toggle.

    Also sets Cache-Control headers on successful responses to reduce
    server load from repeated visits and allow CDN caching.
    """

    showcase_cache_max_age = 300  # 5 minutes

    def dispatch(self, request, *args, **kwargs):
        if not config.SHOWCASE_ENABLED:
            raise Http404
        response = super().dispatch(request, *args, **kwargs)
        patch_cache_control(response, public=True, max_age=self.showcase_cache_max_age)
        return response
