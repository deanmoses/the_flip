"""Tests for wiki home view."""

from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.core.test_utils import (
    SuppressRequestLogsMixin,
    TestDataMixin,
)
from the_flip.apps.wiki.models import WikiPage


@tag("views")
class WikiHomeViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for WikiHomeView."""

    def test_home_returns_200(self):
        """Home page returns 200."""
        self.client.force_login(self.maintainer_user)

        response = self.client.get(reverse("wiki-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Docs")

    def test_home_shows_recent_pages(self):
        """Home page shows recently updated pages."""
        self.client.force_login(self.maintainer_user)

        # Signal auto-creates untagged sentinel
        WikiPage.objects.create(title="Recent Page", slug="recent")

        response = self.client.get(reverse("wiki-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recent Page")

    def test_home_requires_login(self):
        """Unauthenticated users are redirected to login."""
        response = self.client.get(reverse("wiki-home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
