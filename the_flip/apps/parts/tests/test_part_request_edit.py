"""Tests for part request and part request update edit views."""

from datetime import timedelta

from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from the_flip.apps.core.test_utils import (
    DATETIME_INPUT_FORMAT,
    SuppressRequestLogsMixin,
    TestDataMixin,
    create_part_request,
    create_part_request_update,
)


@tag("views")
class PartRequestEditViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for PartRequestEditView."""

    def setUp(self):
        super().setUp()
        self.part_request = create_part_request(
            text="Test part request",
            requested_by=self.maintainer,
        )
        self.edit_url = reverse("part-request-edit", kwargs={"pk": self.part_request.pk})

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

    def test_edit_rejects_empty_requester(self):
        """Edit view rejects submission with no requester name or maintainer."""
        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": "2024-12-31T14:30",
                "requester_name": "",  # Empty requester
                "requester_name_username": "",  # No username selected
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a requester name")

        # Should not have modified the record
        self.part_request.refresh_from_db()
        self.assertEqual(self.part_request.requested_by, self.maintainer)

    def test_edit_rejects_future_date(self):
        """Edit view rejects dates in the future."""
        self.client.force_login(self.maintainer_user)

        future_date = timezone.now() + timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": future_date.strftime(DATETIME_INPUT_FORMAT),
                "requester_name": str(self.maintainer),
                "requester_name_username": self.maintainer_user.username,
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "future")

        # Should not have modified the record
        self.part_request.refresh_from_db()
        self.assertLess(self.part_request.occurred_at, timezone.now())

    def test_edit_accepts_past_date(self):
        """Edit view accepts dates in the past."""
        self.client.force_login(self.maintainer_user)

        past_date = timezone.now() - timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": past_date.strftime(DATETIME_INPUT_FORMAT),
                "requester_name": str(self.maintainer),
                "requester_name_username": self.maintainer_user.username,
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirect on success


@tag("views")
class PartRequestUpdateEditViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for PartRequestUpdateEditView."""

    def setUp(self):
        super().setUp()
        self.part_request = create_part_request(
            text="Test part request",
            requested_by=self.maintainer,
        )
        self.update = create_part_request_update(
            part_request=self.part_request,
            posted_by=self.maintainer,
            text="Initial update",
        )
        self.edit_url = reverse("part-request-update-edit", kwargs={"pk": self.update.pk})

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

    def test_edit_rejects_empty_poster(self):
        """Edit view rejects submission with no poster name or maintainer."""
        self.client.force_login(self.maintainer_user)

        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": "2024-12-31T14:30",
                "poster_name": "",  # Empty poster
                "poster_name_username": "",  # No username selected
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a poster name")

        # Should not have modified the record
        self.update.refresh_from_db()
        self.assertEqual(self.update.posted_by, self.maintainer)

    def test_edit_rejects_future_date(self):
        """Edit view rejects dates in the future."""
        self.client.force_login(self.maintainer_user)

        future_date = timezone.now() + timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": future_date.strftime(DATETIME_INPUT_FORMAT),
                "poster_name": str(self.maintainer),
                "poster_name_username": self.maintainer_user.username,
            },
        )

        # Should return form with error, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "future")

        # Should not have modified the record
        self.update.refresh_from_db()
        self.assertLess(self.update.occurred_at, timezone.now())

    def test_edit_accepts_past_date(self):
        """Edit view accepts dates in the past."""
        self.client.force_login(self.maintainer_user)

        past_date = timezone.now() - timedelta(days=7)
        response = self.client.post(
            self.edit_url,
            {
                "occurred_at": past_date.strftime(DATETIME_INPUT_FORMAT),
                "poster_name": str(self.maintainer),
                "poster_name_username": self.maintainer_user.username,
            },
        )

        self.assertEqual(response.status_code, 302)  # Redirect on success
