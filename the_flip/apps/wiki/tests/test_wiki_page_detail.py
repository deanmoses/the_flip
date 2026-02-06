"""Tests for wiki page detail view."""

from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.core.test_utils import (
    SuppressRequestLogsMixin,
    TestDataMixin,
)
from the_flip.apps.wiki.models import WikiPage, WikiPageTag


@tag("views")
class WikiPageDetailViewTests(SuppressRequestLogsMixin, TestDataMixin, TestCase):
    """Tests for WikiPageDetailView."""

    def test_detail_view_returns_200(self):
        """Valid page path returns 200."""
        self.client.force_login(self.maintainer_user)

        page = WikiPage.objects.create(title="Test Page", slug="test-page")
        WikiPageTag.objects.create(page=page, tag="docs", slug="test-page")

        response = self.client.get(reverse("wiki-page-detail", args=["docs/test-page"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Page")

    def test_detail_view_untagged_page(self):
        """Untagged page (empty tag) returns 200."""
        self.client.force_login(self.maintainer_user)

        # Signal auto-creates untagged sentinel
        WikiPage.objects.create(title="Root Page", slug="root-page")

        response = self.client.get(reverse("wiki-page-detail", args=["root-page"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Root Page")

    def test_detail_view_nested_tag(self):
        """Nested tag path returns 200."""
        self.client.force_login(self.maintainer_user)

        page = WikiPage.objects.create(title="Nested", slug="nested")
        WikiPageTag.objects.create(page=page, tag="machines/blackout", slug="nested")

        response = self.client.get(reverse("wiki-page-detail", args=["machines/blackout/nested"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nested")

    def test_detail_view_missing_page_returns_404(self):
        """Non-existent page returns 404."""
        self.client.force_login(self.maintainer_user)

        response = self.client.get(reverse("wiki-page-detail", args=["does/not/exist"]))

        self.assertEqual(response.status_code, 404)

    def test_detail_view_requires_login(self):
        """Unauthenticated users are redirected to login."""
        # Signal auto-creates untagged sentinel
        WikiPage.objects.create(title="Test", slug="test")

        response = self.client.get(reverse("wiki-page-detail", args=["test"]))

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_detail_view_requires_maintainer(self):
        """Non-maintainer users get 403."""
        self.client.force_login(self.regular_user)

        # Signal auto-creates untagged sentinel
        WikiPage.objects.create(title="Test", slug="test")

        response = self.client.get(reverse("wiki-page-detail", args=["test"]))

        self.assertEqual(response.status_code, 403)
