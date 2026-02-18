"""Tests for maintenance template tags — meta formatters with auth awareness.

Tests the tag functions directly (not through template rendering).
These test the NEW simple_tag signatures with takes_context=True.
"""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, tag

from flipfix.apps.core.test_utils import (
    create_log_entry,
    create_maintainer_user,
    create_problem_report,
)
from flipfix.apps.maintenance.templatetags.maintenance_tags import (
    log_entry_meta,
    problem_report_meta,
)


@tag("views")
class ProblemReportMetaTagTests(TestCase):
    """Tests for problem_report_meta tag with auth awareness."""

    def setUp(self):
        super().setUp()
        self.user = create_maintainer_user(first_name="Alice", last_name="Smith")
        self.report = create_problem_report(reported_by_name="Alice Smith")

    def test_maintainer_sees_reporter_name(self):
        """problem_report_meta for authenticated user includes reporter name."""
        context = {"user": self.user}
        result = problem_report_meta(context, self.report)
        self.assertIn("Alice Smith", str(result))

    def test_guest_sees_timestamp_only(self):
        """problem_report_meta for anonymous user returns timestamp only, no name."""
        context = {"user": AnonymousUser()}
        result = problem_report_meta(context, self.report)
        self.assertNotIn("Alice Smith", str(result))
        # Should still contain a <strong> timestamp
        self.assertIn("<strong>", str(result))


@tag("views")
class LogEntryMetaTagTests(TestCase):
    """Tests for log_entry_meta tag with auth awareness."""

    def setUp(self):
        super().setUp()
        self.user = create_maintainer_user(first_name="Bob", last_name="Jones")
        self.entry = create_log_entry(created_by=self.user)
        self.entry.maintainers.add(self.user.maintainer)

    def test_maintainer_sees_maintainer_name(self):
        """log_entry_meta for authenticated user includes maintainer name."""
        context = {"user": self.user}
        result = log_entry_meta(context, self.entry)
        self.assertIn("Bob Jones", str(result))

    def test_guest_sees_timestamp_only(self):
        """log_entry_meta for anonymous user returns timestamp only, no name."""
        context = {"user": AnonymousUser()}
        result = log_entry_meta(context, self.entry)
        self.assertNotIn("Bob Jones", str(result))
        # Should still contain a <strong> timestamp
        self.assertIn("<strong>", str(result))
