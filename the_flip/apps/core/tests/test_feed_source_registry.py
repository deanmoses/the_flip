"""Tests for the feed source dynamic registry."""

from django.test import TestCase, tag

from the_flip.apps.core.feed import (
    _FEED_SOURCES,
    EntryType,
    FeedEntrySource,
    clear_feed_source_registry,
    get_registered_entry_types,
    register_feed_source,
)


@tag("models")
class FeedSourceRegistryStartupTests(TestCase):
    """Tests that apps register their feed sources via AppConfig.ready()."""

    def test_all_expected_sources_registered(self):
        """All four feed sources are present in the registry after startup."""
        expected = {
            EntryType.LOG,
            EntryType.PROBLEM_REPORT,
            EntryType.PART_REQUEST,
            EntryType.PART_REQUEST_UPDATE,
        }
        self.assertEqual(set(_FEED_SOURCES.keys()), expected)

    def test_registered_values_are_feed_entry_sources(self):
        """Registry stores FeedEntrySource instances."""
        for source in _FEED_SOURCES.values():
            self.assertIsInstance(source, FeedEntrySource)

    def test_each_source_has_callable_queryset_factory(self):
        """Each registered source has a callable get_base_queryset."""
        for source in _FEED_SOURCES.values():
            self.assertTrue(
                callable(source.get_base_queryset),
                f"Source '{source.entry_type}' has non-callable get_base_queryset",
            )

    def test_get_registered_entry_types(self):
        """get_registered_entry_types() returns all registered keys."""
        result = get_registered_entry_types()
        self.assertEqual(set(result), set(_FEED_SOURCES.keys()))


@tag("models")
class RegisterFeedSourceTests(TestCase):
    """Tests for the register/clear API itself.

    These tests clear and restore the registry, so they verify the
    registration mechanics independently of AppConfig.ready().
    """

    def setUp(self):
        self._saved = dict(_FEED_SOURCES)

    def tearDown(self):
        _FEED_SOURCES.clear()
        _FEED_SOURCES.update(self._saved)

    def test_register_adds_source(self):
        """register_feed_source() adds a source keyed by entry_type."""
        clear_feed_source_registry()

        source = FeedEntrySource(
            entry_type="test_type",
            get_base_queryset=lambda: None,
            machine_filter_field="machine",
            global_select_related=(),
        )
        register_feed_source(source)

        self.assertIn("test_type", _FEED_SOURCES)
        self.assertIs(_FEED_SOURCES["test_type"], source)

    def test_duplicate_registration_raises(self):
        """Registering the same entry_type twice raises ValueError."""
        clear_feed_source_registry()

        source = FeedEntrySource(
            entry_type="test_type",
            get_base_queryset=lambda: None,
            machine_filter_field="machine",
            global_select_related=(),
        )
        register_feed_source(source)

        with self.assertRaises(ValueError) as ctx:
            register_feed_source(source)
        self.assertIn("already registered", str(ctx.exception))

    def test_clear_empties_registry(self):
        """clear_feed_source_registry() removes all entries."""
        clear_feed_source_registry()
        self.assertEqual(len(_FEED_SOURCES), 0)

    def test_get_registered_entry_types_after_clear(self):
        """get_registered_entry_types() returns empty tuple after clear."""
        clear_feed_source_registry()
        self.assertEqual(get_registered_entry_types(), ())
