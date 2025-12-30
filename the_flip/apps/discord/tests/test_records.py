"""Tests for Discord record creation."""

from django.test import TestCase, override_settings, tag

from the_flip.apps.core.test_utils import (
    create_machine,
    create_maintainer_user,
    create_part_request,
    create_problem_report,
)
from the_flip.apps.discord.models import DiscordMessageMapping
from the_flip.apps.discord.records import (
    _create_log_entry,
    _create_part_request_update,
)
from the_flip.apps.maintenance.models import LogEntry


@tag("tasks")
class LogEntryParentLinkingTests(TestCase):
    """Tests for log entry linking to parent problem reports."""

    def setUp(self):
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer

    def test_log_entry_links_to_problem_report(self):
        """Log entry created with parent_record_id links to that problem report."""
        problem_report = create_problem_report(machine=self.machine)

        log_entry = _create_log_entry(
            machine=self.machine,
            description="Fixed the issue",
            maintainer=self.maintainer,
            discord_display_name=None,
            parent_record_id=problem_report.pk,
        )

        self.assertEqual(log_entry.problem_report, problem_report)
        self.assertEqual(log_entry.problem_report.pk, problem_report.pk)

    def test_log_entry_without_parent_has_no_problem_report(self):
        """Log entry created without parent_record_id has no linked problem report."""
        log_entry = _create_log_entry(
            machine=self.machine,
            description="Fixed something",
            maintainer=self.maintainer,
            discord_display_name=None,
            parent_record_id=None,
        )

        self.assertIsNone(log_entry.problem_report)

    def test_log_entry_with_nonexistent_parent_has_no_problem_report(self):
        """Log entry with invalid parent_record_id gracefully has no link (logs warning)."""
        log_entry = _create_log_entry(
            machine=self.machine,
            description="Fixed something",
            maintainer=self.maintainer,
            discord_display_name=None,
            parent_record_id=99999,  # Non-existent ID
        )

        # Should not raise, just logs warning and creates without link
        self.assertIsNone(log_entry.problem_report)

    def test_log_entry_uses_maintainer_when_provided(self):
        """Log entry associates maintainer when provided."""
        log_entry = _create_log_entry(
            machine=self.machine,
            description="Fixed the flipper",
            maintainer=self.maintainer,
            discord_display_name="Discord User",
            parent_record_id=None,
        )

        self.assertIn(self.maintainer, log_entry.maintainers.all())
        # maintainer_names should be empty when maintainer is linked
        self.assertEqual(log_entry.maintainer_names, "")

    def test_log_entry_uses_fallback_name_when_no_maintainer(self):
        """Log entry uses discord_display_name as fallback when no maintainer."""
        log_entry = _create_log_entry(
            machine=self.machine,
            description="Fixed the flipper",
            maintainer=None,
            discord_display_name="Discord User",
            parent_record_id=None,
        )

        self.assertEqual(log_entry.maintainers.count(), 0)
        self.assertEqual(log_entry.maintainer_names, "Discord User")

    def test_log_entry_uses_discord_fallback_when_no_display_name(self):
        """Log entry uses 'Discord' as fallback when no maintainer or display name."""
        log_entry = _create_log_entry(
            machine=self.machine,
            description="Fixed the flipper",
            maintainer=None,
            discord_display_name=None,
            parent_record_id=None,
        )

        self.assertEqual(log_entry.maintainer_names, "Discord")


@tag("tasks")
class PartRequestUpdateParentLinkingTests(TestCase):
    """Tests for part request update linking to parent part requests."""

    def setUp(self):
        self.machine = create_machine()
        self.user = create_maintainer_user()
        self.maintainer = self.user.maintainer

    def test_update_links_to_part_request(self):
        """Part request update links to the specified parent part request."""
        part_request = create_part_request(
            machine=self.machine,
            requested_by=self.maintainer,
        )

        update = _create_part_request_update(
            parent_record_id=part_request.pk,
            description="Parts arrived!",
            maintainer=self.maintainer,
        )

        self.assertEqual(update.part_request, part_request)
        self.assertEqual(update.part_request.pk, part_request.pk)

    def test_update_with_nonexistent_parent_raises(self):
        """Part request update with invalid parent_record_id raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _create_part_request_update(
                parent_record_id=99999,  # Non-existent ID
                description="Parts arrived!",
                maintainer=self.maintainer,
            )

        self.assertIn("Part request not found", str(ctx.exception))


@tag("tasks")
@override_settings(SITE_URL="https://flipfix.example.com")
class MultiMessageSourceTrackingTests(TestCase):
    """Tests for marking multiple source messages as processed."""

    def setUp(self):
        self.machine = create_machine()

    def test_all_source_messages_marked_processed(self):
        """All source_message_ids are marked as processed."""
        from asgiref.sync import async_to_sync

        from the_flip.apps.discord.llm import RecordSuggestion, RecordType
        from the_flip.apps.discord.records import create_record
        from the_flip.apps.discord.types import DiscordUserInfo

        # Create suggestion with multiple source message IDs
        author_id = "123456789012345678"  # Discord snowflake format
        suggestion = RecordSuggestion(
            record_type=RecordType.PROBLEM_REPORT,
            description="Flipper broken across multiple messages",
            source_message_ids=["111111111", "222222222", "333333333"],
            author_id=author_id,
            slug=self.machine.slug,
        )

        discord_user = DiscordUserInfo(
            user_id=author_id,
            username="testuser",
            display_name="Test User",
        )
        author_id_map = {author_id: discord_user}

        # Call the async function synchronously
        result = async_to_sync(create_record)(suggestion, author_id, author_id_map)

        # All three messages should be marked as processed
        self.assertTrue(DiscordMessageMapping.is_processed("111111111"))
        self.assertTrue(DiscordMessageMapping.is_processed("222222222"))
        self.assertTrue(DiscordMessageMapping.is_processed("333333333"))

        # Verify all map to the same record
        from the_flip.apps.maintenance.models import ProblemReport

        self.assertTrue(DiscordMessageMapping.has_mapping_for(ProblemReport, result.record_id))

    def test_single_source_message_marked_processed(self):
        """Single source_message_id is marked as processed."""
        from asgiref.sync import async_to_sync

        from the_flip.apps.discord.llm import RecordSuggestion, RecordType
        from the_flip.apps.discord.records import create_record
        from the_flip.apps.discord.types import DiscordUserInfo

        author_id = "234567890123456789"  # Discord snowflake format
        suggestion = RecordSuggestion(
            record_type=RecordType.PROBLEM_REPORT,
            description="Something broken",
            source_message_ids=["999999999"],
            author_id=author_id,
            slug=self.machine.slug,
        )

        discord_user = DiscordUserInfo(
            user_id=author_id,
            username="anotheruser",
            display_name="Another User",
        )
        author_id_map = {author_id: discord_user}

        async_to_sync(create_record)(suggestion, author_id, author_id_map)

        self.assertTrue(DiscordMessageMapping.is_processed("999999999"))

    def test_log_entry_with_parent_links_correctly(self):
        """Log entry created via create_record links to parent problem report."""
        from asgiref.sync import async_to_sync

        from the_flip.apps.discord.llm import RecordSuggestion, RecordType
        from the_flip.apps.discord.records import create_record
        from the_flip.apps.discord.types import DiscordUserInfo

        # Create a problem report to link to
        problem_report = create_problem_report(machine=self.machine)

        author_id = "345678901234567890"  # Discord snowflake format
        suggestion = RecordSuggestion(
            record_type=RecordType.LOG_ENTRY,
            description="Fixed the issue reported earlier",
            source_message_ids=["444444444"],
            author_id=author_id,
            slug=self.machine.slug,
            parent_record_id=problem_report.pk,
        )

        discord_user = DiscordUserInfo(
            user_id=author_id,
            username="fixer",
            display_name="The Fixer",
        )
        author_id_map = {author_id: discord_user}

        result = async_to_sync(create_record)(suggestion, author_id, author_id_map)

        # Verify the log entry links to the problem report
        log_entry = LogEntry.objects.get(pk=result.record_id)
        self.assertEqual(log_entry.problem_report, problem_report)

    def test_log_entry_inherits_machine_from_parent_problem_report(self):
        """Log entry without slug inherits machine from parent problem report."""
        from asgiref.sync import async_to_sync

        from the_flip.apps.discord.llm import RecordSuggestion, RecordType
        from the_flip.apps.discord.records import create_record
        from the_flip.apps.discord.types import DiscordUserInfo

        # Create a problem report on a specific machine
        problem_report = create_problem_report(machine=self.machine)

        author_id = "345678901234567890"
        suggestion = RecordSuggestion(
            record_type=RecordType.LOG_ENTRY,
            description="Fixed the issue",
            source_message_ids=["555555555"],
            author_id=author_id,
            slug=None,  # No machine specified - should inherit from parent
            parent_record_id=problem_report.pk,
        )

        discord_user = DiscordUserInfo(
            user_id=author_id,
            username="fixer",
            display_name="The Fixer",
        )
        author_id_map = {author_id: discord_user}

        result = async_to_sync(create_record)(suggestion, author_id, author_id_map)

        # Verify the log entry is on the same machine as the problem report
        log_entry = LogEntry.objects.get(pk=result.record_id)
        self.assertEqual(log_entry.machine, self.machine)
        self.assertEqual(log_entry.problem_report, problem_report)

    def test_part_request_update_links_correctly(self):
        """Part request update created via create_record links to parent."""
        from asgiref.sync import async_to_sync

        from the_flip.apps.discord.llm import RecordSuggestion, RecordType
        from the_flip.apps.discord.records import create_record
        from the_flip.apps.discord.types import DiscordUserInfo

        user = create_maintainer_user(username="partsuser")
        maintainer = user.maintainer

        # Create a part request to update
        part_request = create_part_request(
            machine=self.machine,
            requested_by=maintainer,
        )

        author_id = "456789012345678901"  # Discord snowflake format
        suggestion = RecordSuggestion(
            record_type=RecordType.PART_REQUEST_UPDATE,
            description="Parts arrived today!",
            source_message_ids=["555555555"],
            author_id=author_id,
            slug=None,  # Optional for updates
            parent_record_id=part_request.pk,
        )

        # Use matching username so maintainer gets linked
        discord_user = DiscordUserInfo(
            user_id=author_id,
            username="partsuser",
            display_name="Parts User",
        )
        author_id_map = {author_id: discord_user}

        result = async_to_sync(create_record)(suggestion, author_id, author_id_map)

        # Verify the update links to the part request
        from the_flip.apps.parts.models import PartRequestUpdate

        update = PartRequestUpdate.objects.get(pk=result.record_id)
        self.assertEqual(update.part_request, part_request)


@tag("discord")
class ResolveAuthorTests(TestCase):
    """Tests for _resolve_author() function."""

    def test_discord_snowflake_resolves_to_discord_user(self):
        """Discord snowflake ID resolves via author_id_map."""
        from the_flip.apps.discord.records import _resolve_author
        from the_flip.apps.discord.types import DiscordUserInfo

        author_id = "123456789012345678"
        discord_user = DiscordUserInfo(
            user_id=author_id,
            username="testuser",
            display_name="Test User",
        )
        author_id_map = {author_id: discord_user}

        maintainer, display_name = _resolve_author(author_id, author_id_map)

        # No maintainer linked yet, but display_name comes from Discord
        self.assertIsNone(maintainer)
        self.assertEqual(display_name, "Test User")

    def test_flipfix_prefix_resolves_by_name(self):
        """flipfix/ prefixed author_id resolves via Maintainer.match_by_name."""
        from the_flip.apps.accounts.models import Maintainer
        from the_flip.apps.discord.records import _resolve_author

        # Create a maintainer with known name
        user = create_maintainer_user(username="sarahchen", first_name="Sarah", last_name="Chen")
        expected_maintainer = Maintainer.objects.get(user=user)

        author_id = "flipfix/Sarah Chen"
        author_id_map: dict = {}  # Empty - flipfix/ prefix doesn't use the map

        maintainer, display_name = _resolve_author(author_id, author_id_map)

        self.assertEqual(maintainer, expected_maintainer)
        self.assertEqual(display_name, "Sarah Chen")

    def test_flipfix_prefix_returns_name_when_no_match(self):
        """flipfix/ prefix returns the name even when no maintainer matches."""
        from the_flip.apps.discord.records import _resolve_author

        author_id = "flipfix/Unknown Person"
        author_id_map: dict = {}

        maintainer, display_name = _resolve_author(author_id, author_id_map)

        self.assertIsNone(maintainer)
        self.assertEqual(display_name, "Unknown Person")

    def test_unknown_author_id_returns_fallback(self):
        """Unknown author_id not in map returns fallback."""
        from the_flip.apps.discord.records import _resolve_author

        author_id = "999999999999999999"
        author_id_map: dict = {}  # Empty map

        maintainer, display_name = _resolve_author(author_id, author_id_map)

        self.assertIsNone(maintainer)
        self.assertEqual(display_name, "Discord")
