"""Tests for public machine detail view.

Maintainer machine feed tests are in test_machine_feed.py.
"""

from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.core.test_utils import create_machine


@tag("views")
class PublicMachineDetailViewTests(TestCase):
    """Tests for public-facing machine detail view."""

    def setUp(self):
        """Set up test data for public views."""
        self.machine = create_machine(slug="public-machine")
        self.detail_url = reverse("public-machine-detail", kwargs={"slug": self.machine.slug})

    def test_public_detail_view_accessible(self):
        """Public detail view should be accessible to anonymous users."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/machine_detail_public.html")

    def test_public_detail_view_displays_machine_details(self):
        """Public detail view should display machine-specific details."""
        response = self.client.get(self.detail_url)
        self.assertContains(response, self.machine.name)
        self.assertContains(response, self.machine.model.manufacturer)
