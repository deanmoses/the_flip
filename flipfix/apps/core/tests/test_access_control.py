"""Tests for global access control (LoginRequiredMiddleware + MaintainerAccessMiddleware).

Hit real app URLs to verify the middleware stack works end-to-end.
"""

from __future__ import annotations

from django.test import tag

from flipfix.apps.core.test_utils import (
    AccessControlTestCase,
    create_maintainer_user,
    create_user,
)


@tag("views")
class LoginRequiredMiddlewareTests(AccessControlTestCase):
    """LoginRequiredMiddleware redirects anonymous users to login."""

    def test_anonymous_get_default_route_redirects_to_login(self):
        """Anonymous GET to a default (maintainer) route redirects to login."""
        response = self.client.get("/parts/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


@tag("views")
class MaintainerAccessMiddlewareTests(AccessControlTestCase):
    """MaintainerAccessMiddleware checks portal permission globally."""

    def setUp(self):
        super().setUp()
        self.maintainer = create_maintainer_user()
        self.regular_user = create_user()

    def test_authenticated_without_portal_permission_gets_403(self):
        """Authenticated user without can_access_maintainer_portal permission gets 403."""
        self.client.force_login(self.regular_user)
        response = self.client.get("/parts/")
        self.assertEqual(response.status_code, 403)

    def test_authenticated_maintainer_gets_200(self):
        """Authenticated maintainer with portal permission gets 200."""
        self.client.force_login(self.maintainer)
        response = self.client.get("/parts/")
        self.assertEqual(response.status_code, 200)


@tag("views")
class AlwaysPublicViewTests(AccessControlTestCase):
    """Views marked access='always_public' bypass both middlewares."""

    def test_healthz_accessible_when_anonymous(self):
        """healthz endpoint returns 200 without authentication."""
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)

    def test_home_accessible_when_anonymous(self):
        """Home page (/) returns 200 without authentication."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
