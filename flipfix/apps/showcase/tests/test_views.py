"""Tests for the public showcase views."""

from __future__ import annotations

from constance.test import override_config
from django.test import TestCase, tag
from django.urls import reverse

from flipfix.apps.core.test_utils import (
    SuppressRequestLogsMixin,
    TestDataMixin,
    create_log_entry,
    create_maintainer_user,
    create_problem_report,
)


class ShowcaseTestMixin(TestDataMixin):
    """Common setup for showcase tests.

    Creates a problem report and log entry on the default machine, with
    identifiable names for anonymization assertions.
    """

    def setUp(self):
        super().setUp()
        self.alice = create_maintainer_user(
            username="alice_maint",
            first_name="Alice",
            last_name="Maintainer",
        )
        self.report = create_problem_report(
            machine=self.machine,
            description="Flipper is stuck",
            reported_by_name="Bob Reporter",
            reported_by_contact="bob@example.com",
        )
        self.log_entry = create_log_entry(
            machine=self.machine,
            text="Adjusted flipper alignment",
            problem_report=self.report,
            created_by=self.alice,
        )


# ──────────────────────────────────────────────
# Toggle tests
# ──────────────────────────────────────────────


@tag("views")
class ShowcaseToggleTests(SuppressRequestLogsMixin, ShowcaseTestMixin, TestCase):
    """SHOWCASE_ENABLED constance toggle controls all showcase URLs."""

    SHOWCASE_URLS = [
        "showcase:machines",
        "showcase:problems",
        "showcase:logs",
    ]

    @override_config(SHOWCASE_ENABLED=False)
    def test_all_urls_return_404_when_disabled(self):
        """Every showcase URL returns 404 when SHOWCASE_ENABLED is False."""
        urls = [
            reverse("showcase:machines"),
            reverse("showcase:machine", kwargs={"slug": self.machine.slug}),
            reverse("showcase:machine-entries", kwargs={"slug": self.machine.slug}),
            reverse("showcase:problems"),
            reverse("showcase:problem", kwargs={"pk": self.report.pk}),
            reverse("showcase:problem-entries", kwargs={"pk": self.report.pk}),
            reverse("showcase:logs"),
            reverse("showcase:log-entries"),
            reverse("showcase:log", kwargs={"pk": self.log_entry.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, f"{url} should return 404 when disabled")

    @override_config(SHOWCASE_ENABLED=True)
    def test_machine_list_returns_200_when_enabled(self):
        """Machine list is accessible when SHOWCASE_ENABLED is True."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertEqual(response.status_code, 200)

    @override_config(SHOWCASE_ENABLED=True)
    def test_problem_board_returns_200_when_enabled(self):
        """Problem board is accessible when SHOWCASE_ENABLED is True."""
        response = self.client.get(reverse("showcase:problems"))
        self.assertEqual(response.status_code, 200)

    @override_config(SHOWCASE_ENABLED=True)
    def test_log_list_returns_200_when_enabled(self):
        """Log list is accessible when SHOWCASE_ENABLED is True."""
        response = self.client.get(reverse("showcase:logs"))
        self.assertEqual(response.status_code, 200)


# ──────────────────────────────────────────────
# Access tests — no login required
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseAccessTests(SuppressRequestLogsMixin, ShowcaseTestMixin, TestCase):
    """All showcase pages are accessible without authentication."""

    def test_machine_list_without_login(self):
        """Machine list works for anonymous visitors."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertEqual(response.status_code, 200)

    def test_machine_feed_without_login(self):
        """Machine feed works for anonymous visitors."""
        response = self.client.get(reverse("showcase:machine", kwargs={"slug": self.machine.slug}))
        self.assertEqual(response.status_code, 200)

    def test_problem_board_without_login(self):
        """Problem board works for anonymous visitors."""
        response = self.client.get(reverse("showcase:problems"))
        self.assertEqual(response.status_code, 200)

    def test_problem_detail_without_login(self):
        """Problem detail works for anonymous visitors."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertEqual(response.status_code, 200)

    def test_log_list_without_login(self):
        """Log list works for anonymous visitors."""
        response = self.client.get(reverse("showcase:logs"))
        self.assertEqual(response.status_code, 200)

    def test_log_detail_without_login(self):
        """Log detail works for anonymous visitors."""
        response = self.client.get(reverse("showcase:log", kwargs={"pk": self.log_entry.pk}))
        self.assertEqual(response.status_code, 200)

    def test_post_returns_405(self):
        """POST requests are rejected on showcase pages."""
        urls = [
            reverse("showcase:machines"),
            reverse("showcase:problems"),
            reverse("showcase:logs"),
        ]
        for url in urls:
            response = self.client.post(url)
            self.assertEqual(response.status_code, 405, f"POST to {url} should return 405")


# ──────────────────────────────────────────────
# Content tests
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseMachineContentTests(ShowcaseTestMixin, TestCase):
    """Machine list and feed render expected content."""

    def test_machine_list_renders_machines(self):
        """Machine list page contains the test machine."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertContains(response, self.machine.name)

    def test_machine_list_uses_correct_template(self):
        """Machine list uses the showcase template."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertTemplateUsed(response, "showcase/machines.html")

    def test_machine_feed_renders_entries(self):
        """Machine feed page contains log entry text."""
        response = self.client.get(reverse("showcase:machine", kwargs={"slug": self.machine.slug}))
        self.assertContains(response, "Adjusted flipper alignment")

    def test_machine_feed_uses_correct_template(self):
        """Machine feed uses the showcase template."""
        response = self.client.get(reverse("showcase:machine", kwargs={"slug": self.machine.slug}))
        self.assertTemplateUsed(response, "showcase/machine.html")

    def test_machine_feed_excludes_parts_filter(self):
        """Machine feed does not show the parts filter tab."""
        response = self.client.get(reverse("showcase:machine", kwargs={"slug": self.machine.slug}))
        self.assertNotContains(response, "Parts")

    def test_machine_feed_partial_returns_json(self):
        """Machine feed AJAX endpoint returns JSON."""
        response = self.client.get(
            reverse(
                "showcase:machine-entries",
                kwargs={"slug": self.machine.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("has_next", data)


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseProblemContentTests(ShowcaseTestMixin, TestCase):
    """Problem board and detail render expected content."""

    def test_problem_board_renders_problems(self):
        """Problem board shows open problem reports."""
        response = self.client.get(reverse("showcase:problems"))
        self.assertContains(response, "Flipper is stuck")

    def test_problem_board_uses_correct_template(self):
        """Problem board uses the showcase template."""
        response = self.client.get(reverse("showcase:problems"))
        self.assertTemplateUsed(response, "showcase/problems.html")

    def test_problem_detail_renders_description(self):
        """Problem detail shows the report description."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertContains(response, "Flipper is stuck")

    def test_problem_detail_uses_correct_template(self):
        """Problem detail uses the showcase template."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertTemplateUsed(response, "showcase/problem.html")

    def test_problem_detail_shows_log_entries(self):
        """Problem detail shows linked log entries."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertContains(response, "Adjusted flipper alignment")

    def test_problem_log_entries_partial_returns_json(self):
        """Problem log entries AJAX endpoint returns JSON."""
        response = self.client.get(
            reverse("showcase:problem-entries", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("has_next", data)


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseLogContentTests(ShowcaseTestMixin, TestCase):
    """Log list and detail render expected content."""

    def test_log_list_renders_entries(self):
        """Log list page contains the test log entry."""
        response = self.client.get(reverse("showcase:logs"))
        self.assertContains(response, "Adjusted flipper alignment")

    def test_log_list_uses_correct_template(self):
        """Log list uses the showcase template."""
        response = self.client.get(reverse("showcase:logs"))
        self.assertTemplateUsed(response, "showcase/logs.html")

    def test_log_detail_renders_text(self):
        """Log detail shows the entry text."""
        response = self.client.get(reverse("showcase:log", kwargs={"pk": self.log_entry.pk}))
        self.assertContains(response, "Adjusted flipper alignment")

    def test_log_detail_uses_correct_template(self):
        """Log detail uses the showcase template."""
        response = self.client.get(reverse("showcase:log", kwargs={"pk": self.log_entry.pk}))
        self.assertTemplateUsed(response, "showcase/log.html")

    def test_log_list_partial_returns_json(self):
        """Log list AJAX endpoint returns JSON."""
        response = self.client.get(reverse("showcase:log-entries"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("has_next", data)

    def test_log_detail_shows_linked_problem(self):
        """Log detail shows linked problem report."""
        response = self.client.get(reverse("showcase:log", kwargs={"pk": self.log_entry.pk}))
        self.assertContains(response, f"Problem Report #{self.report.pk}")


# ──────────────────────────────────────────────
# Anonymization tests
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseAnonymizationTests(ShowcaseTestMixin, TestCase):
    """Showcase pages do not expose maintainer names or reporter info."""

    def test_log_detail_does_not_show_maintainer_names(self):
        """Log detail omits maintainer names."""
        response = self.client.get(reverse("showcase:log", kwargs={"pk": self.log_entry.pk}))
        self.assertNotContains(response, "Alice")
        self.assertNotContains(response, "Maintainer")
        self.assertNotContains(response, "alice_maint")

    def test_machine_feed_does_not_show_maintainer_names(self):
        """Machine feed omits maintainer names."""
        response = self.client.get(reverse("showcase:machine", kwargs={"slug": self.machine.slug}))
        self.assertNotContains(response, "Alice")
        self.assertNotContains(response, "alice_maint")

    def test_problem_detail_does_not_show_reporter_name(self):
        """Problem detail omits the reporter name."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertNotContains(response, "Bob Reporter")

    def test_problem_detail_does_not_show_reporter_contact(self):
        """Problem detail omits the reporter contact info."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertNotContains(response, "bob@example.com")

    def test_log_list_does_not_show_maintainer_names(self):
        """Global log list omits maintainer names."""
        response = self.client.get(reverse("showcase:logs"))
        self.assertNotContains(response, "Alice")
        self.assertNotContains(response, "alice_maint")


# ──────────────────────────────────────────────
# Link tests
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseLinkTests(ShowcaseTestMixin, TestCase):
    """Showcase links point to /visit/ URLs or the public report form."""

    def test_machine_card_links_to_showcase_feed(self):
        """Machine card links to the showcase machine feed."""
        response = self.client.get(reverse("showcase:machines"))
        expected_url = reverse("showcase:machine", kwargs={"slug": self.machine.slug})
        self.assertContains(response, expected_url)

    def test_machine_card_report_links_to_public_form(self):
        """Report Problem button links to the public form, not maintainer form."""
        response = self.client.get(reverse("showcase:machines"))
        expected_url = reverse("public-problem-report-create", kwargs={"slug": self.machine.slug})
        self.assertContains(response, expected_url)

    def test_machine_card_does_not_link_to_maintainer_urls(self):
        """Machine card does not link to maintainer portal."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertNotContains(response, "/machines/test-machine/logs/")
        self.assertNotContains(response, "url 'log-create-machine'")

    def test_problem_detail_breadcrumbs_use_showcase_urls(self):
        """Problem detail breadcrumbs point to showcase URLs."""
        response = self.client.get(reverse("showcase:problem", kwargs={"pk": self.report.pk}))
        self.assertContains(
            response,
            reverse("showcase:machines"),
        )
        self.assertContains(
            response,
            reverse("showcase:machine", kwargs={"slug": self.machine.slug}),
        )

    def test_log_detail_breadcrumbs_use_showcase_urls(self):
        """Log detail breadcrumbs point to showcase URLs."""
        response = self.client.get(reverse("showcase:log", kwargs={"pk": self.log_entry.pk}))
        self.assertContains(
            response,
            reverse("showcase:machines"),
        )
        self.assertContains(
            response,
            reverse("showcase:machine", kwargs={"slug": self.machine.slug}),
        )


# ──────────────────────────────────────────────
# Page bounds and abuse prevention
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcasePageBoundsTests(SuppressRequestLogsMixin, ShowcaseTestMixin, TestCase):
    """Pagination abuse prevention: pages beyond MAX_PAGE return 404."""

    def test_log_list_partial_rejects_excessive_page(self):
        """Log list partial returns 404 for page > MAX_PAGE."""
        response = self.client.get(reverse("showcase:log-entries"), {"page": "101"})
        self.assertEqual(response.status_code, 404)

    def test_problem_log_entries_partial_rejects_excessive_page(self):
        """Problem log entries partial returns 404 for page > MAX_PAGE."""
        response = self.client.get(
            reverse("showcase:problem-entries", kwargs={"pk": self.report.pk}),
            {"page": "101"},
        )
        self.assertEqual(response.status_code, 404)

    def test_machine_feed_partial_rejects_excessive_page(self):
        """Machine feed partial returns 404 for page > MAX_PAGE."""
        response = self.client.get(
            reverse(
                "showcase:machine-entries",
                kwargs={"slug": self.machine.slug},
            ),
            {"page": "101"},
        )
        self.assertEqual(response.status_code, 404)

    def test_machine_feed_partial_rejects_non_positive_page(self):
        """Machine feed partial returns 404 for page < 1."""
        url = reverse("showcase:machine-entries", kwargs={"slug": self.machine.slug})
        for page in ("0", "-1"):
            with self.subTest(page=page):
                response = self.client.get(url, {"page": page})
                self.assertEqual(response.status_code, 404)


# ──────────────────────────────────────────────
# Search engine prevention
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseNoindexTests(ShowcaseTestMixin, TestCase):
    """Showcase pages include noindex meta tag to prevent search engine crawling."""

    def test_machine_list_has_noindex(self):
        """Machine list includes noindex meta tag."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertContains(response, 'name="robots" content="noindex, nofollow"')

    def test_problem_board_has_noindex(self):
        """Problem board includes noindex meta tag."""
        response = self.client.get(reverse("showcase:problems"))
        self.assertContains(response, 'name="robots" content="noindex, nofollow"')

    def test_log_list_has_noindex(self):
        """Log list includes noindex meta tag."""
        response = self.client.get(reverse("showcase:logs"))
        self.assertContains(response, 'name="robots" content="noindex, nofollow"')


# ──────────────────────────────────────────────
# Cache headers
# ──────────────────────────────────────────────


@tag("views")
@override_config(SHOWCASE_ENABLED=True)
class ShowcaseCacheHeaderTests(ShowcaseTestMixin, TestCase):
    """Showcase responses include public cache headers."""

    def test_machine_list_has_cache_control(self):
        """Machine list includes Cache-Control: public, max-age=300."""
        response = self.client.get(reverse("showcase:machines"))
        self.assertIn("max-age=300", response["Cache-Control"])
        self.assertIn("public", response["Cache-Control"])
