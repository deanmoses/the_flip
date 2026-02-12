"""Tests for webhook handler registration and formatting logic."""

from django.test import TestCase, tag

from the_flip.apps.core.test_utils import (
    create_log_entry,
    create_machine,
    create_maintainer_user,
    create_part_request,
    create_part_request_update,
    create_problem_report,
)
from the_flip.apps.discord.webhook_handlers import (
    get_all_webhook_handlers,
    get_webhook_handler,
    get_webhook_handler_by_event,
)
from the_flip.apps.maintenance.models import LogEntry, ProblemReport


@tag("discord")
class WebhookHandlerRegistryTests(TestCase):
    """Tests for webhook handler registration system."""

    def test_all_handlers_registered(self):
        """All expected webhook handlers are registered."""
        handlers = get_all_webhook_handlers()
        handler_names = {h.name for h in handlers}

        expected = {"log_entry", "problem_report", "part_request", "part_request_update"}
        self.assertTrue(
            expected.issubset(handler_names),
            f"Missing handlers: {expected - handler_names}",
        )

    def test_get_webhook_handler_by_name(self):
        """Can retrieve handler by name."""
        handler = get_webhook_handler("log_entry")
        self.assertIsNotNone(handler)
        self.assertEqual(handler.name, "log_entry")

    def test_get_webhook_handler_returns_none_for_unknown(self):
        """Returns None for unknown handler name."""
        handler = get_webhook_handler("nonexistent_handler")
        self.assertIsNone(handler)

    def test_get_webhook_handler_by_event(self):
        """Can retrieve handler by event type."""
        handler = get_webhook_handler_by_event("log_entry_created")
        self.assertIsNotNone(handler)
        self.assertEqual(handler.event_type, "log_entry_created")

    def test_get_webhook_handler_by_event_returns_none_for_unknown(self):
        """Returns None for unknown event type."""
        handler = get_webhook_handler_by_event("unknown_event")
        self.assertIsNone(handler)

    def test_handlers_have_required_attributes(self):
        """All handlers have required attributes."""
        handlers = get_all_webhook_handlers()

        for handler in handlers:
            # Identity attributes
            self.assertTrue(hasattr(handler, "name"))
            self.assertTrue(hasattr(handler, "event_type"))
            self.assertTrue(hasattr(handler, "model_path"))
            self.assertIsInstance(handler.name, str)
            self.assertIsInstance(handler.event_type, str)
            self.assertIsInstance(handler.model_path, str)

            # Display attributes
            self.assertTrue(hasattr(handler, "display_name"))
            self.assertTrue(hasattr(handler, "emoji"))
            self.assertTrue(hasattr(handler, "color"))
            self.assertIsInstance(handler.display_name, str)
            self.assertIsInstance(handler.emoji, str)
            self.assertIsInstance(handler.color, int)

            # Methods
            self.assertTrue(callable(handler.get_detail_url))
            self.assertTrue(callable(handler.format_webhook_message))
            self.assertTrue(callable(handler.get_model_class))
            self.assertTrue(callable(handler.get_object))

    def test_event_types_end_with_created(self):
        """Event types follow naming convention."""
        handlers = get_all_webhook_handlers()

        for handler in handlers:
            self.assertTrue(
                handler.event_type.endswith("_created"),
                f"Handler {handler.name} event type should end with '_created': {handler.event_type}",
            )


@tag("discord")
class LogEntryWebhookHandlerTests(TestCase):
    """Tests for LogEntryWebhookHandler."""

    def setUp(self):
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.handler = get_webhook_handler("log_entry")

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "log_entry")
        self.assertEqual(self.handler.event_type, "log_entry_created")
        self.assertEqual(self.handler.model_path, "maintenance.LogEntry")
        self.assertEqual(self.handler.display_name, "Log Entry")
        self.assertEqual(self.handler.emoji, "🗒️")
        self.assertIsInstance(self.handler.color, int)

    def test_get_model_class(self):
        """Returns correct Django model class."""
        model_class = self.handler.get_model_class()
        self.assertEqual(model_class, LogEntry)

    def test_get_object_with_select_related(self):
        """get_object includes select_related optimization."""
        log_entry = create_log_entry(machine=self.machine, created_by=self.user)

        # This should use select_related to avoid additional queries
        with self.assertNumQueries(1):
            obj = self.handler.get_object(log_entry.pk)
            # Access related objects - should not trigger new queries
            _ = obj.machine
            # Accessing maintainers uses prefetch_related, so we check it separately

        self.assertEqual(obj.pk, log_entry.pk)

    def test_get_object_returns_none_for_nonexistent(self):
        """get_object returns None for nonexistent ID."""
        obj = self.handler.get_object(99999)
        self.assertIsNone(obj)

    def test_format_webhook_message_structure(self):
        """format_webhook_message returns valid Discord webhook structure."""
        log_entry = create_log_entry(machine=self.machine, created_by=self.user)

        message = self.handler.format_webhook_message(log_entry)

        # Should have embeds key
        self.assertIn("embeds", message)
        self.assertIsInstance(message["embeds"], list)
        self.assertGreater(len(message["embeds"]), 0)

        # First embed should have required fields
        embed = message["embeds"][0]
        self.assertIn("title", embed)
        self.assertIn("description", embed)
        self.assertIn("url", embed)
        self.assertIn("color", embed)

    def test_get_detail_url(self):
        """Returns correct detail URL."""
        log_entry = create_log_entry(machine=self.machine, created_by=self.user)

        url = self.handler.get_detail_url(log_entry)

        self.assertIn("/logs/", url)
        self.assertIn(str(log_entry.pk), url)

    def test_should_notify_only_on_creation(self):
        """should_notify returns True only for creation."""
        self.assertTrue(self.handler.should_notify(None, created=True))
        self.assertFalse(self.handler.should_notify(None, created=False))


@tag("discord")
class ProblemReportWebhookHandlerTests(TestCase):
    """Tests for ProblemReportWebhookHandler."""

    def setUp(self):
        self.machine = create_machine()
        self.handler = get_webhook_handler("problem_report")

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "problem_report")
        self.assertEqual(self.handler.event_type, "problem_report_created")
        self.assertEqual(self.handler.model_path, "maintenance.ProblemReport")
        self.assertEqual(self.handler.display_name, "Problem Report")
        self.assertEqual(self.handler.emoji, "⚠️")
        self.assertIsInstance(self.handler.color, int)

    def test_get_model_class(self):
        """Returns correct Django model class."""
        model_class = self.handler.get_model_class()
        self.assertEqual(model_class, ProblemReport)

    def test_get_object_with_select_related(self):
        """get_object includes select_related optimization."""
        report = create_problem_report(machine=self.machine)

        # This should use select_related to avoid additional queries
        with self.assertNumQueries(1):
            obj = self.handler.get_object(report.pk)
            # Access related machine - should not trigger new query
            _ = obj.machine

        self.assertEqual(obj.pk, report.pk)

    def test_format_webhook_message_structure(self):
        """format_webhook_message returns valid Discord webhook structure."""
        report = create_problem_report(machine=self.machine)

        message = self.handler.format_webhook_message(report)

        # Should have embeds key
        self.assertIn("embeds", message)
        self.assertIsInstance(message["embeds"], list)
        self.assertGreater(len(message["embeds"]), 0)

        # First embed should have required fields
        embed = message["embeds"][0]
        self.assertIn("title", embed)
        self.assertIn("description", embed)
        self.assertIn("url", embed)
        self.assertIn("color", embed)

    def test_get_detail_url(self):
        """Returns correct detail URL."""
        report = create_problem_report(machine=self.machine)

        url = self.handler.get_detail_url(report)

        self.assertIn("/problem-reports/", url)
        self.assertIn(str(report.pk), url)


@tag("discord")
class PartRequestWebhookHandlerTests(TestCase):
    """Tests for PartRequestWebhookHandler."""

    def setUp(self):
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer
        self.handler = get_webhook_handler("part_request")

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "part_request")
        self.assertEqual(self.handler.event_type, "part_request_created")
        self.assertEqual(self.handler.model_path, "parts.PartRequest")
        self.assertEqual(self.handler.display_name, "Parts Request")
        self.assertEqual(self.handler.emoji, "📦")
        self.assertIsInstance(self.handler.color, int)

    def test_format_webhook_message_structure(self):
        """format_webhook_message returns valid Discord webhook structure."""
        part_request = create_part_request(
            machine=self.machine,
            requested_by=self.maintainer,
        )

        message = self.handler.format_webhook_message(part_request)

        # Should have embeds key
        self.assertIn("embeds", message)
        self.assertIsInstance(message["embeds"], list)
        self.assertGreater(len(message["embeds"]), 0)

        # First embed should have required fields
        embed = message["embeds"][0]
        self.assertIn("title", embed)
        self.assertIn("description", embed)
        self.assertIn("url", embed)
        self.assertIn("color", embed)

    def test_get_detail_url(self):
        """Returns correct detail URL."""
        part_request = create_part_request(
            machine=self.machine,
            requested_by=self.maintainer,
        )

        url = self.handler.get_detail_url(part_request)

        self.assertIn("/parts/", url)
        self.assertIn(str(part_request.pk), url)


@tag("discord")
class PartRequestUpdateWebhookHandlerTests(TestCase):
    """Tests for PartRequestUpdateWebhookHandler."""

    def setUp(self):
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer
        self.handler = get_webhook_handler("part_request_update")

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "part_request_update")
        self.assertEqual(self.handler.event_type, "part_request_update_created")
        self.assertEqual(self.handler.model_path, "parts.PartRequestUpdate")
        self.assertEqual(self.handler.display_name, "Parts Request Update")
        self.assertEqual(self.handler.emoji, "💬")
        self.assertIsInstance(self.handler.color, int)

    def test_format_webhook_message_structure(self):
        """format_webhook_message returns valid Discord webhook structure."""
        part_request = create_part_request(
            machine=self.machine,
            requested_by=self.maintainer,
        )
        update = create_part_request_update(
            part_request=part_request,
            posted_by=self.maintainer,
            text="Update text",
        )

        message = self.handler.format_webhook_message(update)

        # Should have embeds key
        self.assertIn("embeds", message)
        self.assertIsInstance(message["embeds"], list)
        self.assertGreater(len(message["embeds"]), 0)

        # First embed should have required fields
        embed = message["embeds"][0]
        self.assertIn("title", embed)
        self.assertIn("description", embed)
        self.assertIn("url", embed)
        self.assertIn("color", embed)

    def test_get_detail_url_points_to_parent(self):
        """Detail URL points to parent part request."""
        part_request = create_part_request(
            machine=self.machine,
            requested_by=self.maintainer,
        )
        update = create_part_request_update(
            part_request=part_request,
            posted_by=self.maintainer,
            text="Update text",
        )

        url = self.handler.get_detail_url(update)

        # Should point to parent part request, not update
        self.assertIn("/parts/", url)
        self.assertIn(str(part_request.pk), url)


@tag("discord")
class WebhookHandlerQueryOptimizationTests(TestCase):
    """Tests for webhook handler query optimization."""

    def setUp(self):
        self.machine = create_machine()
        self.user = create_maintainer_user()

    def test_log_entry_handler_prefetches_maintainers(self):
        """LogEntry handler prefetches maintainers to avoid N+1 queries."""
        handler = get_webhook_handler("log_entry")
        log_entry = create_log_entry(machine=self.machine, created_by=self.user)

        # Add maintainer to the log entry
        log_entry.maintainers.add(self.user.maintainer)

        # Fetch with handler's optimization
        with self.assertNumQueries(2):  # One for object, one for prefetch
            obj = handler.get_object(log_entry.pk)
            # Accessing prefetched maintainers should not trigger new queries
            _ = list(obj.maintainers.all())

    def test_log_entry_handler_selects_related_machine(self):
        """LogEntry handler selects related machine."""
        handler = get_webhook_handler("log_entry")
        log_entry = create_log_entry(machine=self.machine, created_by=self.user)

        # Fetch with handler's optimization
        with self.assertNumQueries(1):
            obj = handler.get_object(log_entry.pk)
            # Accessing machine should not trigger new query
            _ = obj.machine

    def test_part_request_update_handler_selects_related_fields(self):
        """PartRequestUpdate handler selects related part_request and machine."""
        handler = get_webhook_handler("part_request_update")
        part_request = create_part_request(
            machine=self.machine,
            requested_by=self.user.maintainer,
        )
        update = create_part_request_update(
            part_request=part_request,
            posted_by=self.user.maintainer,
            text="Update text",
        )

        # Fetch with handler's optimization
        with self.assertNumQueries(1):
            obj = handler.get_object(update.pk)
            # Accessing related objects should not trigger new queries
            _ = obj.part_request
            _ = obj.part_request.machine