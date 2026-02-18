"""Tests for parts template tags — meta formatters with auth awareness.

Tests the tag functions directly (not through template rendering).
"""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, tag

from flipfix.apps.core.test_utils import (
    create_maintainer_user,
    create_part_request,
    create_part_request_update,
)
from flipfix.apps.parts.templatetags.parts_tags import (
    part_request_meta,
    part_update_meta,
)


@tag("templatetags")
class PartRequestMetaTagTests(TestCase):
    """Tests for part_request_meta tag with auth awareness."""

    def setUp(self):
        super().setUp()
        self.user = create_maintainer_user(first_name="Alice", last_name="Smith")
        self.part_request = create_part_request(requested_by=self.user.maintainer)

    def test_maintainer_sees_requester_name(self):
        """part_request_meta for authenticated user includes requester name."""
        context = {"user": self.user}
        result = part_request_meta(context, self.part_request)
        self.assertIn("Alice Smith", str(result))

    def test_guest_sees_timestamp_only(self):
        """part_request_meta for anonymous user returns timestamp only, no name."""
        context = {"user": AnonymousUser()}
        result = part_request_meta(context, self.part_request)
        self.assertNotIn("Alice Smith", str(result))
        # Should still contain a <strong> timestamp
        self.assertIn("<strong>", str(result))

    def test_none_returns_empty(self):
        """part_request_meta with None returns empty string."""
        context = {"user": self.user}
        result = part_request_meta(context, None)
        self.assertEqual(result, "")


@tag("templatetags")
class PartUpdateMetaTagTests(TestCase):
    """Tests for part_update_meta tag with auth awareness."""

    def setUp(self):
        super().setUp()
        self.user = create_maintainer_user(first_name="Bob", last_name="Jones")
        self.update = create_part_request_update(posted_by=self.user.maintainer)

    def test_maintainer_sees_poster_name(self):
        """part_update_meta for authenticated user includes poster name."""
        context = {"user": self.user}
        result = part_update_meta(context, self.update)
        self.assertIn("Bob Jones", str(result))

    def test_guest_sees_timestamp_only(self):
        """part_update_meta for anonymous user returns timestamp only, no name."""
        context = {"user": AnonymousUser()}
        result = part_update_meta(context, self.update)
        self.assertNotIn("Bob Jones", str(result))
        # Should still contain a <strong> timestamp
        self.assertIn("<strong>", str(result))

    def test_none_returns_empty(self):
        """part_update_meta with None returns empty string."""
        context = {"user": self.user}
        result = part_update_meta(context, None)
        self.assertEqual(result, "")
