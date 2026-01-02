"""Tests for the global log entry list view (/logs/).

Machine-scoped log tests are in catalog/tests/test_machine_feed.py.
"""

from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.core.test_utils import (
    TestDataMixin,
    create_log_entry,
    create_problem_report,
)


@tag("views")
class LogListSearchTests(TestDataMixin, TestCase):
    """Tests for global log list search."""

    def setUp(self):
        super().setUp()
        self.list_url = reverse("log-list")

    def test_search_includes_problem_report_description(self):
        """Search should match attached problem report description."""
        report = create_problem_report(machine=self.machine, description="Coil stop broken")
        log_with_report = create_log_entry(
            machine=self.machine,
            text="Investigated noisy coil",
            problem_report=report,
        )
        create_log_entry(machine=self.machine, text="Adjusted flipper alignment")

        self.client.force_login(self.maintainer_user)
        response = self.client.get(self.list_url, {"q": "coil stop"})

        self.assertContains(response, log_with_report.text)
        self.assertContains(response, "Problem:")
        self.assertContains(response, "Coil stop broken")
        self.assertNotContains(response, "Adjusted flipper alignment")

    def test_search_includes_maintainer_names(self):
        """Search should match free-text maintainer names."""
        log_with_name = create_log_entry(
            machine=self.machine,
            text="Replaced coil",
            maintainer_names="Wandering Willie",
        )
        create_log_entry(machine=self.machine, text="Adjusted flipper alignment")

        self.client.force_login(self.maintainer_user)
        response = self.client.get(self.list_url, {"q": "Wandering"})

        self.assertContains(response, log_with_name.text)
        self.assertNotContains(response, "Adjusted flipper alignment")
