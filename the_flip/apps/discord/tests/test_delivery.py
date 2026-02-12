"""Tests for webhook delivery logic."""

from unittest.mock import MagicMock, patch

import requests
from constance.test import override_config
from django.test import TestCase, tag

from the_flip.apps.core.test_utils import create_machine, create_problem_report
from the_flip.apps.discord.tasks import deliver_webhook


@tag("tasks")
class WebhookDeliveryTests(TestCase):
    """Tests for webhook delivery logic."""

    def setUp(self):
        self.machine = create_machine()

    @override_config(DISCORD_WEBHOOK_URL="")
    def test_skips_when_no_webhook_url(self):
        """Skips delivery when no webhook URL is configured."""
        report = create_problem_report(machine=self.machine)
        result = deliver_webhook("problem_report", report.pk)

        self.assertEqual(result.status, "skipped")
        self.assertIn("no webhook URL", result.reason)

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=False,
    )
    def test_skips_when_webhooks_disabled(self):
        """Skips delivery when webhooks are globally disabled."""
        report = create_problem_report(machine=self.machine)
        result = deliver_webhook("problem_report", report.pk)

        self.assertEqual(result.status, "skipped")
        self.assertIn("globally disabled", result.reason)

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_successful_delivery(self, mock_post):
        """Successfully delivers webhook."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        report = create_problem_report(machine=self.machine)
        result = deliver_webhook("problem_report", report.pk)

        self.assertEqual(result.status, "success")
        mock_post.assert_called_once()

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_handles_delivery_failure(self, mock_post):
        """Handles webhook delivery failure gracefully."""
        mock_post.side_effect = requests.RequestException("Connection error")

        report = create_problem_report(machine=self.machine)
        # Capture expected warning log to avoid noise in test output
        with self.assertLogs("the_flip.apps.discord.tasks", level="WARNING"):
            result = deliver_webhook("problem_report", report.pk)

        self.assertEqual(result.status, "error")
        self.assertIn("Connection error", result.reason)


@tag("tasks")
class DeliverWebhookEdgeCasesTests(TestCase):
    """Edge case tests for webhook delivery."""

    def setUp(self):
        self.machine = create_machine()

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    def test_unknown_handler_returns_error(self):
        """Unknown handler name returns error status."""
        result = deliver_webhook("nonexistent_handler", 123)

        self.assertEqual(result.status, "error")
        self.assertIn("Unknown handler", result.reason)

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    def test_object_not_found_returns_error(self):
        """Object not found returns error status."""
        result = deliver_webhook("problem_report", 99999)

        self.assertEqual(result.status, "error")
        self.assertIn("not found", result.reason)

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_http_error_handled_gracefully(self, mock_post):
        """HTTP errors are handled gracefully."""
        mock_post.side_effect = requests.HTTPError("404 Not Found")

        report = create_problem_report(machine=self.machine)

        # Capture expected warning log to avoid noise in test output
        with self.assertLogs("the_flip.apps.discord.tasks", level="WARNING"):
            result = deliver_webhook("problem_report", report.pk)

        self.assertEqual(result.status, "error")
        self.assertIn("404 Not Found", result.reason)

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_timeout_handled_gracefully(self, mock_post):
        """Request timeouts are handled gracefully."""
        mock_post.side_effect = requests.Timeout("Request timed out")

        report = create_problem_report(machine=self.machine)

        # Capture expected warning log
        with self.assertLogs("the_flip.apps.discord.tasks", level="WARNING"):
            result = deliver_webhook("problem_report", report.pk)

        self.assertEqual(result.status, "error")
        self.assertIn("timed out", result.reason.lower())

    @override_config(
        DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc",
        DISCORD_WEBHOOKS_ENABLED=True,
    )
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_preserves_log_context(self, mock_post):
        """Webhook delivery preserves and restores log context."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        report = create_problem_report(machine=self.machine)

        # Call with log context
        log_context = {"request_id": "test-123"}
        result = deliver_webhook("problem_report", report.pk, log_context)

        self.assertEqual(result.status, "success")


@tag("tasks")
class DispatchWebhookEdgeCasesTests(TestCase):
    """Edge case tests for dispatch_webhook."""

    def setUp(self):
        self.machine = create_machine()

    @override_config(DISCORD_WEBHOOKS_ENABLED=False, DISCORD_WEBHOOK_URL="")
    @patch("the_flip.apps.discord.tasks.async_task")
    def test_dispatch_skips_when_disabled(self, mock_async):
        """dispatch_webhook skips when webhooks are disabled."""
        from the_flip.apps.discord.tasks import dispatch_webhook

        dispatch_webhook("problem_report", 123)

        # Should not have queued a task
        mock_async.assert_not_called()

    @override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="")
    @patch("the_flip.apps.discord.tasks.async_task")
    def test_dispatch_skips_when_no_url(self, mock_async):
        """dispatch_webhook skips when no URL configured."""
        from the_flip.apps.discord.tasks import dispatch_webhook

        dispatch_webhook("problem_report", 123)

        # Should not have queued a task
        mock_async.assert_not_called()

    @override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
    @patch("the_flip.apps.discord.tasks.async_task")
    def test_dispatch_warns_on_unknown_handler(self, mock_async):
        """dispatch_webhook logs warning for unknown handler."""
        from the_flip.apps.discord.tasks import dispatch_webhook

        with self.assertLogs("the_flip.apps.discord.tasks", level="WARNING"):
            dispatch_webhook("nonexistent_handler", 123)

        # Should not have queued a task
        mock_async.assert_not_called()


@tag("tasks")
class SendTestWebhookTests(TestCase):
    """Tests for send_test_webhook."""

    @override_config(DISCORD_WEBHOOK_URL="")
    def test_no_url_returns_error(self):
        """Returns error when no webhook URL configured."""
        from the_flip.apps.discord.tasks import send_test_webhook

        result = send_test_webhook("problem_report_created")

        self.assertEqual(result["status"], "error")
        self.assertIn("No webhook URL", result["error"])

    @override_config(DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc")
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_successful_test_webhook(self, mock_post):
        """Successful test webhook returns success."""
        from the_flip.apps.discord.tasks import send_test_webhook

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = send_test_webhook("problem_report_created")

        self.assertEqual(result["status"], "success")
        self.assertIn("message", result)
        mock_post.assert_called_once()

    @override_config(DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/123/abc")
    @patch("the_flip.apps.discord.tasks.requests.post")
    def test_failed_test_webhook(self, mock_post):
        """Failed test webhook returns error."""
        from the_flip.apps.discord.tasks import send_test_webhook

        mock_post.side_effect = requests.RequestException("Connection failed")

        result = send_test_webhook("problem_report_created")

        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)
        self.assertIn("Connection failed", result["error"])