"""Tests for parts feature flag behavior."""

from constance.test import override_config
from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.catalog.feed import (
    ENTRY_TYPE_PART_REQUEST,
    ENTRY_TYPE_PART_REQUEST_UPDATE,
    get_machine_feed_page,
)
from the_flip.apps.core.test_utils import (
    TestDataMixin,
    create_part_request,
)


@tag("views")
class PartsFeatureFlagTests(TestDataMixin, TestCase):
    """Tests for the PARTS_ENABLED feature flag."""

    def test_nav_link_hidden_when_disabled(self):
        """Parts nav link is hidden when PARTS_ENABLED is False."""
        self.client.force_login(self.maintainer_user)

        with override_config(PARTS_ENABLED=False):
            response = self.client.get(reverse("maintainer-machine-list"))
            # The nav link to parts should not be present
            self.assertNotContains(response, 'href="/parts/"')

    def test_nav_link_shown_when_enabled(self):
        """Parts nav link is shown when PARTS_ENABLED is True."""
        self.client.force_login(self.maintainer_user)

        with override_config(PARTS_ENABLED=True):
            response = self.client.get(reverse("maintainer-machine-list"))
            # The nav link to parts should be present
            self.assertContains(response, 'href="/parts/"')

    def test_activity_feed_excludes_parts_when_disabled(self):
        """Machine activity feed excludes parts when PARTS_ENABLED is False."""
        # Create a part request for this machine
        create_part_request(
            text="Test part",
            requested_by=self.maintainer,
            machine=self.machine,
        )

        with override_config(PARTS_ENABLED=False):
            # Get feed with parts entry types
            entries, _ = get_machine_feed_page(
                self.machine,
                entry_types=(ENTRY_TYPE_PART_REQUEST, ENTRY_TYPE_PART_REQUEST_UPDATE),
                page_num=1,
            )
            # No parts should be returned when feature is disabled
            self.assertEqual(entries, [])

    def test_activity_feed_includes_parts_when_enabled(self):
        """Machine activity feed includes parts when PARTS_ENABLED is True."""
        # Create a part request for this machine
        part = create_part_request(
            text="Test part",
            requested_by=self.maintainer,
            machine=self.machine,
        )

        with override_config(PARTS_ENABLED=True):
            # Get feed with parts entry types
            entries, _ = get_machine_feed_page(
                self.machine,
                entry_types=(ENTRY_TYPE_PART_REQUEST, ENTRY_TYPE_PART_REQUEST_UPDATE),
                page_num=1,
            )
            # Parts should be included
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].pk, part.pk)
