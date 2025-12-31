"""Tests for problem report edit view."""

from datetime import timedelta

from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from the_flip.apps.core.test_utils import (
    DATETIME_INPUT_FORMAT,
    SuppressRequestLogsMixin,
    TestDataMixin,
    create_problem_report,
)


@tag("views")
class ProblemReportEditViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for ProblemReportEditView."""

    def setUp(self):
        super().setUp()
        self.problem_report = create_problem_report(machine=self.machine)
        self.edit_url = reverse("problem-report-edit", kwargs={"pk": self.problem_report.pk})

    def test_edit_view_requires_staff(self):
        """Edit view requires staff permission."""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_view_accessible_to_staff(self):
        """Staff can access edit view."""
        self.client.force_login(self.maintainer_user)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_rejects_future_date(self):
        """Edit view rejects dates in the future."""
        self.client.force_login(self.maintainer_user)

        future_date = timezone.now() + timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": future_date.strftime(DATETIME_INPUT_FORMAT),
                "reporter_name": "Test Reporter",
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "future")

        # Should not have modified the record
        self.problem_report.refresh_from_db()
        self.assertLess(self.problem_report.occurred_at, timezone.now())

    def test_edit_accepts_past_date(self):
        """Edit view accepts dates in the past."""
        self.client.force_login(self.maintainer_user)

        past_date = timezone.now() - timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": past_date.strftime(DATETIME_INPUT_FORMAT),
                "reporter_name": "Test Reporter",
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirect on success

    def test_edit_rejects_empty_reporter(self):
        """Edit view rejects submission with no reporter name or user."""
        # First, set up a problem report with a known reporter
        self.problem_report.reported_by_user = self.maintainer_user
        self.problem_report.save()

        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": timezone.now().strftime(DATETIME_INPUT_FORMAT),
                "reporter_name": "",  # Empty reporter
                "reporter_name_username": "",  # No username selected
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a reporter name")

        # Should not have modified the record
        self.problem_report.refresh_from_db()
        self.assertEqual(self.problem_report.reported_by_user, self.maintainer_user)
