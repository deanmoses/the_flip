"""Tests for log entry edit view."""

from datetime import timedelta

from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from the_flip.apps.accounts.models import Maintainer
from the_flip.apps.core.test_utils import (
    DATETIME_INPUT_FORMAT,
    SuppressRequestLogsMixin,
    TestDataMixin,
    create_log_entry,
    create_maintainer_user,
)
from the_flip.apps.maintenance.models import LogEntry


@tag("views")
class LogEntryEditViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for LogEntryEditView."""

    def setUp(self):
        super().setUp()
        self.log_entry = create_log_entry(machine=self.machine, text="Test entry")
        self.log_entry.maintainers.add(self.maintainer)
        self.edit_url = reverse("log-entry-edit", kwargs={"pk": self.log_entry.pk})

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
                "maintainer_usernames": self.maintainer_user.username,
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "future")

        # Should not have modified the record
        self.log_entry.refresh_from_db()
        self.assertLess(self.log_entry.occurred_at, timezone.now())

    def test_edit_accepts_past_date(self):
        """Edit view accepts dates in the past."""
        self.client.force_login(self.maintainer_user)

        past_date = timezone.now() - timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": past_date.strftime(DATETIME_INPUT_FORMAT),
                "maintainer_usernames": self.maintainer_user.username,
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirect on success


@tag("views")
class LogEntryEditMaintainersTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for editing log entry maintainers via chip input."""

    def setUp(self):
        super().setUp()
        self.maintainer2 = create_maintainer_user(
            username="maintainer2", first_name="Second", last_name="Maintainer"
        )
        self.log_entry = LogEntry.objects.create(
            machine=self.machine,
            text="Initial work",
            occurred_at=timezone.now(),
            created_by=self.maintainer_user,
        )
        self.log_entry.maintainers.add(Maintainer.objects.get(user=self.maintainer_user))
        self.edit_url = reverse("log-entry-edit", kwargs={"pk": self.log_entry.pk})

    def test_edit_preserves_maintainers_when_unchanged(self):
        """Editing without changing maintainers preserves existing ones."""
        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": timezone.now().strftime(DATETIME_INPUT_FORMAT),
                "maintainer_usernames": self.maintainer_user.username,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.maintainers.count(), 1)
        self.assertIn(
            Maintainer.objects.get(user=self.maintainer_user),
            self.log_entry.maintainers.all(),
        )

    def test_edit_adds_maintainer(self):
        """Can add a new maintainer via edit."""
        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": timezone.now().strftime(DATETIME_INPUT_FORMAT),
                "maintainer_usernames": [
                    self.maintainer_user.username,
                    self.maintainer2.username,
                ],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.maintainers.count(), 2)

    def test_edit_removes_maintainer(self):
        """Can remove a maintainer via edit."""
        # Start with two maintainers
        self.log_entry.maintainers.add(Maintainer.objects.get(user=self.maintainer2))
        self.assertEqual(self.log_entry.maintainers.count(), 2)

        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": timezone.now().strftime(DATETIME_INPUT_FORMAT),
                "maintainer_usernames": self.maintainer_user.username,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.maintainers.count(), 1)
        self.assertNotIn(
            Maintainer.objects.get(user=self.maintainer2),
            self.log_entry.maintainers.all(),
        )

    def test_edit_clears_all_maintainers(self):
        """Can clear all maintainers via edit."""
        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": timezone.now().strftime(DATETIME_INPUT_FORMAT),
                # No maintainer_usernames submitted
            },
        )

        self.assertEqual(response.status_code, 302)
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.maintainers.count(), 0)

    def test_edit_updates_freetext_names(self):
        """Can update freetext maintainer names via edit."""
        self.log_entry.maintainer_names = "Old Name"
        self.log_entry.maintainers.clear()
        self.log_entry.save()

        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": timezone.now().strftime(DATETIME_INPUT_FORMAT),
                "maintainer_freetext": "New Name",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.log_entry.refresh_from_db()
        self.assertEqual(self.log_entry.maintainer_names, "New Name")
