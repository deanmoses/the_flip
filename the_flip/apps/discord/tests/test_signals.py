"""Tests for webhook signal triggers."""

from unittest.mock import patch

from constance.test import override_config
from django.test import TestCase, tag

from the_flip.apps.accounts.models import Maintainer
from the_flip.apps.core.test_utils import (
    create_log_entry,
    create_machine,
    create_maintainer_user,
    create_part_request,
    create_part_request_update,
    create_problem_report,
)
from the_flip.apps.discord.models import DiscordMessageMapping
from the_flip.apps.maintenance.models import ProblemReport


@tag("tasks")
@override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
class WebhookSignalTests(TestCase):
    """Tests for webhook signal triggers."""

    def setUp(self):
        self.machine = create_machine()

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_fires_on_problem_report_created(self, mock_async):
        """Signal fires when a problem report is created."""
        # All webhook signals use transaction.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            report = ProblemReport.objects.create(
                machine=self.machine,
                description="Test problem",
            )

        mock_async.assert_called()
        call_args = mock_async.call_args
        self.assertEqual(call_args[0][1], "problem_report")
        self.assertEqual(call_args[0][2], report.pk)

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_fires_on_log_entry_created(self, mock_async):
        """Signal fires when a log entry is created."""
        maintainer_user = create_maintainer_user()

        # Log entry signal uses transaction.on_commit, so we need to capture and execute
        with self.captureOnCommitCallbacks(execute=True):
            log_entry = create_log_entry(machine=self.machine, created_by=maintainer_user)

        # Find the log_entry call
        calls = [c for c in mock_async.call_args_list if c[0][1] == "log_entry"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][2], log_entry.pk)


@tag("tasks")
@override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
class PartRequestWebhookSignalTests(TestCase):
    """Tests for part request webhook signal triggers."""

    def setUp(self):
        self.maintainer_user = create_maintainer_user()
        self.maintainer = Maintainer.objects.get(user=self.maintainer_user)
        self.machine = create_machine()

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_fires_on_part_request_created(self, mock_async):
        """Signal fires when a part request is created."""
        # All webhook signals use transaction.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            part_request = create_part_request(
                requested_by=self.maintainer,
                machine=self.machine,
            )

        # Find the part_request call
        calls = [c for c in mock_async.call_args_list if c[0][1] == "part_request"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][2], part_request.pk)

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_fires_on_part_request_update_created(self, mock_async):
        """Signal fires when a part request update is created."""
        with self.captureOnCommitCallbacks(execute=True):
            part_request = create_part_request(requested_by=self.maintainer)
        mock_async.reset_mock()

        # All webhook signals use transaction.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            update = create_part_request_update(
                part_request=part_request,
                posted_by=self.maintainer,
                text="Update text",
            )

        # Find the part_request_update call
        calls = [c for c in mock_async.call_args_list if c[0][1] == "part_request_update"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][2], update.pk)

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_fires_on_status_change_via_update(self, mock_async):
        """Status change via update only fires update_created (not a separate status event)."""
        from the_flip.apps.parts.models import PartRequest

        with self.captureOnCommitCallbacks(execute=True):
            part_request = create_part_request(requested_by=self.maintainer)
        mock_async.reset_mock()

        # All webhook signals use transaction.on_commit
        with self.captureOnCommitCallbacks(execute=True):
            create_part_request_update(
                part_request=part_request,
                posted_by=self.maintainer,
                text="Ordered it",
                new_status=PartRequest.Status.ORDERED,
            )

        # Should only fire part_request_update (status info is included in the update message)
        handler_names = [c[0][1] for c in mock_async.call_args_list]
        self.assertIn("part_request_update", handler_names)
        self.assertNotIn("part_request_status_changed", handler_names)


@tag("tasks")
@override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
class DiscordOriginatedRecordTests(TestCase):
    """Tests that webhooks are NOT dispatched for Discord-originated records.

    When the Discord bot creates a record in Flipfix, we don't want to
    post it back to Discord via webhook (that would be redundant).
    """

    def setUp(self):
        self.machine = create_machine()

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_skips_discord_originated_problem_report(self, mock_async):
        """No webhook when ProblemReport was created from Discord."""
        with self.captureOnCommitCallbacks(execute=True):
            report = create_problem_report(machine=self.machine)
            # Mark as Discord-originated BEFORE transaction commits
            DiscordMessageMapping.mark_processed("discord_msg_123", report)

        # Should NOT have fired problem_report webhook
        calls = [c for c in mock_async.call_args_list if c[0][1] == "problem_report"]
        self.assertEqual(len(calls), 0, "Webhook should not fire for Discord-originated record")

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_skips_discord_originated_log_entry(self, mock_async):
        """No webhook when LogEntry was created from Discord."""
        maintainer_user = create_maintainer_user()

        with self.captureOnCommitCallbacks(execute=True):
            log_entry = create_log_entry(machine=self.machine, created_by=maintainer_user)
            # Mark as Discord-originated BEFORE transaction commits
            DiscordMessageMapping.mark_processed("discord_msg_456", log_entry)

        # Should NOT have fired log_entry webhook
        calls = [c for c in mock_async.call_args_list if c[0][1] == "log_entry"]
        self.assertEqual(len(calls), 0, "Webhook should not fire for Discord-originated record")

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_skips_discord_originated_part_request(self, mock_async):
        """No webhook when PartRequest was created from Discord."""
        maintainer_user = create_maintainer_user()
        maintainer = Maintainer.objects.get(user=maintainer_user)

        with self.captureOnCommitCallbacks(execute=True):
            part_request = create_part_request(
                requested_by=maintainer,
                machine=self.machine,
            )
            # Mark as Discord-originated BEFORE transaction commits
            DiscordMessageMapping.mark_processed("discord_msg_789", part_request)

        # Should NOT have fired part_request webhook
        calls = [c for c in mock_async.call_args_list if c[0][1] == "part_request"]
        self.assertEqual(len(calls), 0, "Webhook should not fire for Discord-originated record")


@tag("tasks")
@override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
class SignalTransactionBehaviorTests(TestCase):
    """Tests for signal transaction.on_commit behavior."""

    def setUp(self):
        self.machine = create_machine()

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_uses_transaction_on_commit(self, mock_async):
        """Signal uses transaction.on_commit to ensure atomic behavior."""
        # Create within transaction context
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            report = ProblemReport.objects.create(
                machine=self.machine,
                description="Test problem",
            )

        # Should have callback but not executed yet
        self.assertEqual(len(callbacks), 1)
        mock_async.assert_not_called()

        # Execute the callback
        for callback in callbacks:
            callback()

        # Now should be called
        mock_async.assert_called_once()

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_signal_not_fired_on_rollback(self, mock_async):
        """Signal is not fired if transaction is rolled back."""
        from django.db import transaction

        try:
            with transaction.atomic():
                ProblemReport.objects.create(
                    machine=self.machine,
                    description="Test problem",
                )
                # Force a rollback
                raise Exception("Intentional rollback")
        except Exception:
            pass

        # Signal should not have been called after rollback
        mock_async.assert_not_called()


@tag("tasks")
@override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
class MultipleRecordCreationTests(TestCase):
    """Tests for multiple records created in sequence."""

    def setUp(self):
        self.machine = create_machine()
        self.maintainer_user = create_maintainer_user()
        self.maintainer = Maintainer.objects.get(user=self.maintainer_user)

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_multiple_problem_reports_fire_separate_webhooks(self, mock_async):
        """Creating multiple problem reports fires separate webhook for each."""
        with self.captureOnCommitCallbacks(execute=True):
            report1 = create_problem_report(machine=self.machine)
            report2 = create_problem_report(machine=self.machine)

        # Should have two problem_report calls
        problem_report_calls = [c for c in mock_async.call_args_list if c[0][1] == "problem_report"]
        self.assertEqual(len(problem_report_calls), 2)

        # Should be for different object IDs
        ids = {c[0][2] for c in problem_report_calls}
        self.assertEqual(ids, {report1.pk, report2.pk})

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_related_records_fire_separate_webhooks(self, mock_async):
        """Creating problem report and log entry fires webhook for each."""
        with self.captureOnCommitCallbacks(execute=True):
            report = create_problem_report(machine=self.machine)
            log_entry = create_log_entry(
                machine=self.machine,
                created_by=self.maintainer_user,
                problem_report=report,
            )

        # Should have both webhooks
        handler_names = [c[0][1] for c in mock_async.call_args_list]
        self.assertIn("problem_report", handler_names)
        self.assertIn("log_entry", handler_names)

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_part_request_and_update_fire_separate_webhooks(self, mock_async):
        """Creating part request and update fires webhook for each."""
        with self.captureOnCommitCallbacks(execute=True):
            part_request = create_part_request(
                requested_by=self.maintainer,
                machine=self.machine,
            )

        mock_async.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            update = create_part_request_update(
                part_request=part_request,
                posted_by=self.maintainer,
                text="Update text",
            )

        # Should have part_request_update webhook
        handler_names = [c[0][1] for c in mock_async.call_args_list]
        self.assertIn("part_request_update", handler_names)


@tag("tasks")
@override_config(DISCORD_WEBHOOKS_ENABLED=True, DISCORD_WEBHOOK_URL="https://test.webhook")
class DiscordMessageMappingCreationTimingTests(TestCase):
    """Tests for Discord message mapping creation timing with signals."""

    def setUp(self):
        self.machine = create_machine()

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_mapping_created_before_commit_prevents_webhook(self, mock_async):
        """Mapping created before commit prevents webhook from firing."""
        with self.captureOnCommitCallbacks(execute=True):
            report = create_problem_report(machine=self.machine)
            # Mark as Discord-originated WITHIN the same transaction
            DiscordMessageMapping.mark_processed("discord_msg_test", report)

        # Should NOT have fired webhook
        calls = [c for c in mock_async.call_args_list if c[0][1] == "problem_report"]
        self.assertEqual(len(calls), 0, "Webhook should not fire when mapping exists")

    @patch("the_flip.apps.discord.tasks.async_task")
    def test_mapping_created_after_commit_does_not_affect_webhook(self, mock_async):
        """Mapping created after commit doesn't prevent webhook that already fired."""
        with self.captureOnCommitCallbacks(execute=True):
            report = create_problem_report(machine=self.machine)
            # Don't create mapping yet

        # Webhook should have fired
        calls = [c for c in mock_async.call_args_list if c[0][1] == "problem_report"]
        self.assertEqual(len(calls), 1, "Webhook should fire when no mapping exists")

        # Creating mapping after the fact doesn't retroactively prevent anything
        DiscordMessageMapping.mark_processed("discord_msg_after", report)

        # Webhook count should remain the same (already fired)
        calls_after = [c for c in mock_async.call_args_list if c[0][1] == "problem_report"]
        self.assertEqual(len(calls_after), 1)