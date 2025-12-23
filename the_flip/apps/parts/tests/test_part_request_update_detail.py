"""Tests for part request update detail view."""

from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.core.test_utils import (
    SuppressRequestLogsMixin,
    TestDataMixin,
    create_part_request,
    create_part_request_update,
)
from the_flip.apps.parts.models import PartRequest


@tag("views")
class PartRequestUpdateDetailViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for PartRequestUpdateDetailView access control and content."""

    def setUp(self):
        super().setUp()
        self.part_request = create_part_request(
            text="Test part request",
            requested_by=self.maintainer,
        )
        self.update = create_part_request_update(
            part_request=self.part_request,
            text="Test update text",
            posted_by=self.maintainer,
        )
        self.detail_url = reverse("part-request-update-detail", kwargs={"pk": self.update.pk})

    def test_detail_view_requires_auth(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)

    def test_detail_view_requires_staff(self):
        """Non-staff users get 403."""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 403)

    def test_detail_view_accessible_to_staff(self):
        """Staff can access detail view."""
        self.client.force_login(self.maintainer_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_detail_shows_update_content(self):
        """Detail page displays update text."""
        self.client.force_login(self.maintainer_user)
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Test update text")

    def test_detail_shows_part_request_link(self):
        """Detail page links back to parent part request."""
        self.client.force_login(self.maintainer_user)
        response = self.client.get(self.detail_url)

        # Should contain link to part request detail
        expected_url = reverse("part-request-detail", kwargs={"pk": self.part_request.pk})
        self.assertContains(response, expected_url)
        self.assertContains(response, f"#{self.part_request.pk}")

    def test_detail_shows_status_change(self):
        """Detail page shows status change if present."""
        update_with_status = create_part_request_update(
            part_request=self.part_request,
            text="Status changed",
            posted_by=self.maintainer,
            new_status=PartRequest.Status.ORDERED,
        )
        detail_url = reverse("part-request-update-detail", kwargs={"pk": update_with_status.pk})

        self.client.force_login(self.maintainer_user)
        response = self.client.get(detail_url)

        self.assertContains(response, "Status Change")
        self.assertContains(response, "Ordered")
