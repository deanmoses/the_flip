"""Tests for bot handler registration and creation logic."""

from django.test import TestCase, tag
from django.utils import timezone as django_timezone

from the_flip.apps.core.test_utils import (
    create_machine,
    create_maintainer_user,
    create_part_request,
    create_problem_report,
)
from the_flip.apps.discord.bot_handlers import (
    get_all_bot_handlers,
    get_bot_handler,
    register,
)
from the_flip.apps.discord.bot_handlers.log_entry import LogEntryBotHandler
from the_flip.apps.discord.bot_handlers.part_request import PartRequestBotHandler
from the_flip.apps.discord.bot_handlers.part_request_update import (
    PartRequestUpdateBotHandler,
)
from the_flip.apps.discord.bot_handlers.problem_report import ProblemReportBotHandler
from the_flip.apps.discord.llm import RecordType
from the_flip.apps.maintenance.models import LogEntry, ProblemReport
from the_flip.apps.parts.models import PartRequest, PartRequestUpdate


@tag("discord")
class BotHandlerRegistryTests(TestCase):
    """Tests for bot handler registration system."""

    def test_all_handlers_registered(self):
        """All expected bot handlers are registered."""
        handlers = get_all_bot_handlers()
        handler_names = {h.name for h in handlers}

        expected = {"log_entry", "problem_report", "part_request", "part_request_update"}
        self.assertTrue(
            expected.issubset(handler_names),
            f"Missing handlers: {expected - handler_names}",
        )

    def test_get_bot_handler_by_name(self):
        """Can retrieve handler by name."""
        handler = get_bot_handler("log_entry")
        self.assertIsNotNone(handler)
        self.assertEqual(handler.name, "log_entry")

    def test_get_bot_handler_returns_none_for_unknown(self):
        """Returns None for unknown handler name."""
        handler = get_bot_handler("nonexistent_handler")
        self.assertIsNone(handler)

    def test_handlers_have_required_attributes(self):
        """All handlers have required attributes."""
        handlers = get_all_bot_handlers()

        for handler in handlers:
            # Identity attributes
            self.assertTrue(hasattr(handler, "name"))
            self.assertTrue(hasattr(handler, "display_name"))
            self.assertIsInstance(handler.name, str)
            self.assertIsInstance(handler.display_name, str)

            # LLM schema attributes
            self.assertTrue(hasattr(handler, "machine_required"))
            self.assertIsInstance(handler.machine_required, bool)

            # Methods
            self.assertTrue(callable(handler.create_from_suggestion))
            self.assertTrue(callable(handler.get_detail_url))

    def test_handler_record_type_property(self):
        """Handler record_type property returns correct RecordType enum."""
        handler = get_bot_handler("log_entry")
        self.assertEqual(handler.record_type, RecordType.LOG_ENTRY)

        handler = get_bot_handler("problem_report")
        self.assertEqual(handler.record_type, RecordType.PROBLEM_REPORT)


@tag("discord")
class LogEntryBotHandlerTests(TestCase):
    """Tests for LogEntryBotHandler."""

    def setUp(self):
        self.handler = LogEntryBotHandler()
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "log_entry")
        self.assertEqual(self.handler.display_name, "Log Entry")
        self.assertTrue(self.handler.machine_required)
        self.assertEqual(self.handler.parent_handler_name, "problem_report")
        self.assertIsNone(self.handler.child_type_name)
        self.assertEqual(self.handler.media_model_name, "LogEntryMedia")
        self.assertIsNotNone(self.handler.url_pattern)

    def test_create_basic_log_entry(self):
        """Creates basic log entry with required fields."""
        log_entry = self.handler.create_from_suggestion(
            description="Fixed the flipper",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        self.assertIsInstance(log_entry, LogEntry)
        self.assertEqual(log_entry.text, "Fixed the flipper")
        self.assertEqual(log_entry.machine, self.machine)
        self.assertIn(self.maintainer, log_entry.maintainers.all())

    def test_create_without_machine_raises(self):
        """Creating without machine raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Fixed something",
                machine=None,
                maintainer=self.maintainer,
                display_name="Test User",
                parent_record_id=None,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Machine is required", str(ctx.exception))

    def test_get_detail_url(self):
        """Returns correct detail URL."""
        log_entry = self.handler.create_from_suggestion(
            description="Fixed the flipper",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        url = self.handler.get_detail_url(log_entry)

        self.assertIn("/logs/", url)
        self.assertIn(str(log_entry.pk), url)

    def test_url_pattern_matches_detail_url(self):
        """URL pattern matches the generated detail URL."""
        from django.urls import reverse

        log_entry = self.handler.create_from_suggestion(
            description="Fixed the flipper",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        # Generate URL using Django reverse
        url_path = reverse("log-detail", kwargs={"pk": log_entry.pk})

        # URL pattern should match
        match = self.handler.url_pattern.match(url_path.rstrip("/"))
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), log_entry.pk)


@tag("discord")
class ProblemReportBotHandlerTests(TestCase):
    """Tests for ProblemReportBotHandler."""

    def setUp(self):
        self.handler = ProblemReportBotHandler()
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "problem_report")
        self.assertEqual(self.handler.display_name, "Problem Report")
        self.assertTrue(self.handler.machine_required)
        self.assertIsNone(self.handler.parent_handler_name)
        self.assertEqual(self.handler.child_type_name, "log_entry")
        self.assertEqual(self.handler.media_model_name, "ProblemReportMedia")
        self.assertIsNotNone(self.handler.url_pattern)

    def test_create_basic_problem_report(self):
        """Creates basic problem report with required fields."""
        report = self.handler.create_from_suggestion(
            description="Flipper is broken",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        self.assertIsInstance(report, ProblemReport)
        self.assertEqual(report.description, "Flipper is broken")
        self.assertEqual(report.machine, self.machine)
        self.assertEqual(report.problem_type, ProblemReport.ProblemType.OTHER)

    def test_create_without_machine_raises(self):
        """Creating without machine raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Something broken",
                machine=None,
                maintainer=self.maintainer,
                display_name="Test User",
                parent_record_id=None,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Machine is required", str(ctx.exception))

    def test_create_with_maintainer_links_user(self):
        """Creating with maintainer links reported_by_user."""
        report = self.handler.create_from_suggestion(
            description="Flipper is broken",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        self.assertEqual(report.reported_by_user, self.maintainer.user)
        self.assertEqual(report.reported_by_name, "")

    def test_create_without_maintainer_uses_display_name(self):
        """Creating without maintainer uses display_name."""
        report = self.handler.create_from_suggestion(
            description="Flipper is broken",
            machine=self.machine,
            maintainer=None,
            display_name="Anonymous User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        self.assertIsNone(report.reported_by_user)
        self.assertEqual(report.reported_by_name, "Anonymous User")

    def test_get_detail_url(self):
        """Returns correct detail URL."""
        report = self.handler.create_from_suggestion(
            description="Flipper is broken",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        url = self.handler.get_detail_url(report)

        self.assertIn("/problem-reports/", url)
        self.assertIn(str(report.pk), url)


@tag("discord")
class PartRequestBotHandlerTests(TestCase):
    """Tests for PartRequestBotHandler."""

    def setUp(self):
        self.handler = PartRequestBotHandler()
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "part_request")
        self.assertEqual(self.handler.display_name, "Part Request")
        self.assertFalse(self.handler.machine_required)
        self.assertIsNone(self.handler.parent_handler_name)
        self.assertEqual(self.handler.child_type_name, "part_request_update")
        self.assertEqual(self.handler.media_model_name, "PartRequestMedia")
        self.assertIsNotNone(self.handler.url_pattern)

    def test_create_part_request_with_machine(self):
        """Creates part request with machine."""
        part_request = self.handler.create_from_suggestion(
            description="Need flipper rubbers",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        self.assertIsInstance(part_request, PartRequest)
        self.assertEqual(part_request.text, "Need flipper rubbers")
        self.assertEqual(part_request.machine, self.machine)
        self.assertEqual(part_request.requested_by, self.maintainer)

    def test_create_part_request_without_machine(self):
        """Creates part request without machine (machine is optional)."""
        part_request = self.handler.create_from_suggestion(
            description="Need general supplies",
            machine=None,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        self.assertIsNone(part_request.machine)
        self.assertEqual(part_request.requested_by, self.maintainer)

    def test_create_without_maintainer_raises(self):
        """Creating without maintainer raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Need parts",
                machine=self.machine,
                maintainer=None,
                display_name="Test User",
                parent_record_id=None,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Cannot create part request without a linked maintainer", str(ctx.exception))

    def test_get_detail_url(self):
        """Returns correct detail URL."""
        part_request = self.handler.create_from_suggestion(
            description="Need flipper rubbers",
            machine=self.machine,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=None,
            occurred_at=django_timezone.now(),
        )

        url = self.handler.get_detail_url(part_request)

        self.assertIn("/parts/", url)
        self.assertIn(str(part_request.pk), url)


@tag("discord")
class PartRequestUpdateBotHandlerTests(TestCase):
    """Tests for PartRequestUpdateBotHandler."""

    def setUp(self):
        self.handler = PartRequestUpdateBotHandler()
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer
        self.part_request = create_part_request(
            machine=self.machine,
            requested_by=self.maintainer,
        )

    def test_handler_attributes(self):
        """Handler has correct attributes."""
        self.assertEqual(self.handler.name, "part_request_update")
        self.assertEqual(self.handler.display_name, "Part Request Update")
        self.assertFalse(self.handler.machine_required)
        self.assertEqual(self.handler.parent_handler_name, "part_request")
        self.assertIsNone(self.handler.child_type_name)
        self.assertEqual(self.handler.media_model_name, "PartRequestUpdateMedia")
        self.assertIsNone(self.handler.url_pattern)  # No distinct URL pattern

    def test_create_update(self):
        """Creates part request update linked to parent."""
        update = self.handler.create_from_suggestion(
            description="Parts arrived!",
            machine=None,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=self.part_request.pk,
            occurred_at=django_timezone.now(),
        )

        self.assertIsInstance(update, PartRequestUpdate)
        self.assertEqual(update.text, "Parts arrived!")
        self.assertEqual(update.part_request, self.part_request)
        self.assertEqual(update.posted_by, self.maintainer)

    def test_create_without_parent_raises(self):
        """Creating without parent_record_id raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Update text",
                machine=None,
                maintainer=self.maintainer,
                display_name="Test User",
                parent_record_id=None,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("requires parent_record_id", str(ctx.exception))

    def test_create_with_invalid_parent_raises(self):
        """Creating with nonexistent parent raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Update text",
                machine=None,
                maintainer=self.maintainer,
                display_name="Test User",
                parent_record_id=99999,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Part request not found", str(ctx.exception))

    def test_create_without_maintainer_raises(self):
        """Creating without maintainer raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Update text",
                machine=None,
                maintainer=None,
                display_name="Test User",
                parent_record_id=self.part_request.pk,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Cannot create part request update without a linked maintainer", str(ctx.exception))

    def test_get_detail_url_points_to_parent(self):
        """Detail URL points to parent part request."""
        update = self.handler.create_from_suggestion(
            description="Parts arrived!",
            machine=None,
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=self.part_request.pk,
            occurred_at=django_timezone.now(),
        )

        url = self.handler.get_detail_url(update)

        # URL should point to parent part request
        self.assertIn("/parts/", url)
        self.assertIn(str(self.part_request.pk), url)


@tag("discord")
class ParentChildHandlerRelationshipTests(TestCase):
    """Tests for parent-child relationships between handlers."""

    def test_log_entry_has_problem_report_parent(self):
        """LogEntry handler specifies problem_report as parent."""
        handler = get_bot_handler("log_entry")
        self.assertEqual(handler.parent_handler_name, "problem_report")

    def test_problem_report_has_log_entry_child(self):
        """ProblemReport handler specifies log_entry as child type."""
        handler = get_bot_handler("problem_report")
        self.assertEqual(handler.child_type_name, "log_entry")

    def test_part_request_update_has_part_request_parent(self):
        """PartRequestUpdate handler specifies part_request as parent."""
        handler = get_bot_handler("part_request_update")
        self.assertEqual(handler.parent_handler_name, "part_request")

    def test_part_request_has_update_child(self):
        """PartRequest handler specifies part_request_update as child type."""
        handler = get_bot_handler("part_request")
        self.assertEqual(handler.child_type_name, "part_request_update")

    def test_parent_child_handlers_can_be_retrieved(self):
        """Parent and child handlers can be retrieved by name."""
        log_entry_handler = get_bot_handler("log_entry")
        parent_name = log_entry_handler.parent_handler_name

        # Should be able to retrieve parent handler
        parent_handler = get_bot_handler(parent_name)
        self.assertIsNotNone(parent_handler)
        self.assertEqual(parent_handler.name, "problem_report")

        # Parent's child type should match log entry
        self.assertEqual(parent_handler.child_type_name, "log_entry")


@tag("discord")
class LogEntryInheritsParentMachineTests(TestCase):
    """Tests for log entry inheriting machine from parent problem report."""

    def setUp(self):
        self.handler = LogEntryBotHandler()
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer

    def test_inherits_machine_from_parent_when_no_machine_specified(self):
        """Log entry without machine inherits from parent problem report."""
        # Create parent problem report
        problem_report = create_problem_report(machine=self.machine)

        # Create log entry without machine, but with parent
        log_entry = self.handler.create_from_suggestion(
            description="Fixed the issue",
            machine=None,  # No machine specified
            maintainer=self.maintainer,
            display_name="Test User",
            parent_record_id=problem_report.pk,
            occurred_at=django_timezone.now(),
        )

        # Should inherit machine from parent
        self.assertEqual(log_entry.machine, self.machine)
        self.assertEqual(log_entry.problem_report, problem_report)

    def test_raises_when_no_machine_and_no_valid_parent(self):
        """Raises ValueError when no machine and parent doesn't exist."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Fixed the issue",
                machine=None,
                maintainer=self.maintainer,
                display_name="Test User",
                parent_record_id=99999,  # Nonexistent parent
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Machine is required", str(ctx.exception))

    def test_raises_when_no_machine_and_no_parent(self):
        """Raises ValueError when no machine and no parent specified."""
        with self.assertRaises(ValueError) as ctx:
            self.handler.create_from_suggestion(
                description="Fixed the issue",
                machine=None,
                maintainer=self.maintainer,
                display_name="Test User",
                parent_record_id=None,
                occurred_at=django_timezone.now(),
            )

        self.assertIn("Machine is required", str(ctx.exception))