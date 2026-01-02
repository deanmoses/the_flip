"""Tests for PartRequest and PartRequestUpdate search methods.

These tests verify search consistency between Parts models and maintenance
models (LogEntry, ProblemReport), ensuring all models search the same
field types (username, first/last name, freetext names, linked records).
"""

from django.test import TestCase, tag

from the_flip.apps.core.test_utils import (
    TestDataMixin,
    create_maintainer_user,
    create_part_request,
    create_part_request_update,
)
from the_flip.apps.parts.models import PartRequest, PartRequestUpdate


@tag("models")
class PartRequestSearchUsernameTests(TestDataMixin, TestCase):
    """Tests for username search in PartRequest.

    Verifies that PartRequest searches requester's username, matching
    the pattern used by LogEntry and ProblemReport for their user FK fields.
    """

    def test_search_matches_requester_username(self):
        """Search should match requester's username."""
        requester = create_maintainer_user(
            username="techguy",
            first_name="",
            last_name="",
        )
        matching = create_part_request(
            machine=self.machine,
            text="Need a flipper coil",
            requested_by=requester.maintainer,
        )
        create_part_request(machine=self.machine, text="Need a rubber ring")

        results = list(PartRequest.objects.search("techguy"))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)

    def test_search_for_machine_matches_requester_username(self):
        """Machine-scoped search should match requester's username."""
        requester = create_maintainer_user(
            username="fixerman",
            first_name="",
            last_name="",
        )
        matching = create_part_request(
            machine=self.machine,
            text="Need a coil",
            requested_by=requester.maintainer,
        )
        create_part_request(machine=self.machine, text="Need a bulb")

        results = list(
            PartRequest.objects.filter(machine=self.machine).search_for_machine("fixerman")
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)


@tag("models")
class PartRequestUpdateSearchUsernameTests(TestDataMixin, TestCase):
    """Tests for username search in PartRequestUpdate.

    Verifies that PartRequestUpdate searches poster's username, matching
    the pattern used by LogEntry for maintainer usernames.
    """

    def test_search_for_machine_matches_poster_username(self):
        """Machine-scoped search should match poster's username."""
        poster = create_maintainer_user(
            username="partsmaster",
            first_name="",
            last_name="",
        )
        part_request = create_part_request(machine=self.machine)
        matching = create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Part has been ordered",
        )
        create_part_request_update(
            part_request=part_request,
            text="Still waiting",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request__machine=self.machine).search_for_machine(
                "partsmaster"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)


@tag("models")
class PartRequestUpdateSearchForPartRequestTests(TestDataMixin, TestCase):
    """Tests for search_for_part_request() in PartRequestUpdate.

    Verifies that PartRequestUpdate.search_for_part_request() searches poster's
    username, first_name, last_name, and freetext name, matching the pattern
    used by LogEntry.search_for_problem_report() for maintainer fields.
    """

    def test_search_for_part_request_matches_poster_username(self):
        """Part-request-scoped search should match poster's username."""
        poster = create_maintainer_user(
            username="alexparts",
            first_name="",
            last_name="",
        )
        part_request = create_part_request(machine=self.machine)
        matching = create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Part ordered",
        )
        create_part_request_update(
            part_request=part_request,
            text="Still waiting",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request=part_request).search_for_part_request(
                "alexparts"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)

    def test_search_for_part_request_matches_poster_first_name(self):
        """Part-request-scoped search should match poster's first name."""
        poster = create_maintainer_user(
            username="user1",
            first_name="Alexander",
            last_name="",
        )
        part_request = create_part_request(machine=self.machine)
        matching = create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Part ordered",
        )
        create_part_request_update(
            part_request=part_request,
            text="Still waiting",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request=part_request).search_for_part_request(
                "Alexander"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)

    def test_search_for_part_request_matches_poster_last_name(self):
        """Part-request-scoped search should match poster's last name."""
        poster = create_maintainer_user(
            username="user1",
            first_name="",
            last_name="Smithson",
        )
        part_request = create_part_request(machine=self.machine)
        matching = create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Part ordered",
        )
        create_part_request_update(
            part_request=part_request,
            text="Still waiting",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request=part_request).search_for_part_request(
                "Smithson"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)

    def test_search_for_part_request_matches_poster_freetext_name(self):
        """Part-request-scoped search should match poster's freetext name."""
        part_request = create_part_request(machine=self.machine)
        matching = create_part_request_update(
            part_request=part_request,
            posted_by=None,
            posted_by_name="Wandering Willie",
            text="Part ordered",
        )
        create_part_request_update(
            part_request=part_request,
            text="Still waiting",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request=part_request).search_for_part_request(
                "Wandering"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)

    def test_search_for_part_request_matches_update_text(self):
        """Part-request-scoped search should match update text."""
        part_request = create_part_request(machine=self.machine)
        matching = create_part_request_update(
            part_request=part_request,
            text="Ordered from Marco Specialties",
        )
        create_part_request_update(
            part_request=part_request,
            text="Still waiting",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request=part_request).search_for_part_request(
                "Marco"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matching)


@tag("models")
class PartRequestLinkedRecordSearchTests(TestDataMixin, TestCase):
    """Tests for linked record search in PartRequest.

    Verifies that PartRequest.search_for_machine() searches linked updates,
    matching how ProblemReport.search_for_machine() searches linked log_entries.
    """

    def test_search_for_machine_matches_update_text(self):
        """Machine-scoped search should match linked update text."""
        part_request = create_part_request(
            machine=self.machine,
            text="Need a flipper coil",
        )
        create_part_request_update(
            part_request=part_request,
            text="Ordered from Marco Specialties",
        )
        create_part_request(machine=self.machine, text="Need a rubber ring")

        results = list(PartRequest.objects.filter(machine=self.machine).search_for_machine("Marco"))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], part_request)

    def test_search_for_machine_matches_update_poster_username(self):
        """Machine-scoped search should match linked update poster's username."""
        poster = create_maintainer_user(
            username="ordermaster",
            first_name="",
            last_name="",
        )
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
        )
        create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Ordered",
        )
        create_part_request(machine=self.machine, text="Need a bulb")

        results = list(
            PartRequest.objects.filter(machine=self.machine).search_for_machine("ordermaster")
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], part_request)

    def test_search_for_machine_matches_update_poster_first_name(self):
        """Machine-scoped search should match linked update poster's first name."""
        poster = create_maintainer_user(
            username="user1",
            first_name="Wanda",
            last_name="",
        )
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
        )
        create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Ordered",
        )
        create_part_request(machine=self.machine, text="Need a bulb")

        results = list(PartRequest.objects.filter(machine=self.machine).search_for_machine("Wanda"))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], part_request)

    def test_search_for_machine_matches_update_poster_last_name(self):
        """Machine-scoped search should match linked update poster's last name."""
        poster = create_maintainer_user(
            username="user1",
            first_name="",
            last_name="Techworthy",
        )
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
        )
        create_part_request_update(
            part_request=part_request,
            posted_by=poster.maintainer,
            text="Ordered",
        )
        create_part_request(machine=self.machine, text="Need a bulb")

        results = list(
            PartRequest.objects.filter(machine=self.machine).search_for_machine("Techworthy")
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], part_request)

    def test_search_for_machine_matches_update_poster_freetext_name(self):
        """Machine-scoped search should match linked update poster's freetext name."""
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
        )
        create_part_request_update(
            part_request=part_request,
            posted_by=None,
            posted_by_name="Wandering Willie",
            text="Ordered",
        )
        create_part_request(machine=self.machine, text="Need a bulb")

        results = list(
            PartRequest.objects.filter(machine=self.machine).search_for_machine("Wandering")
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], part_request)


@tag("models")
class PartRequestUpdateLinkedRecordSearchTests(TestDataMixin, TestCase):
    """Tests for linked record search in PartRequestUpdate.

    Verifies that PartRequestUpdate.search_for_machine() searches the parent
    part_request, matching how LogEntry.search_for_machine() searches the
    linked problem_report description and reporter name.
    """

    def test_search_for_machine_matches_parent_text(self):
        """Machine-scoped search should match parent part request text."""
        part_request = create_part_request(
            machine=self.machine,
            text="Need a flipper coil for left side",
        )
        update = create_part_request_update(
            part_request=part_request,
            text="Part ordered",
        )
        other_request = create_part_request(
            machine=self.machine,
            text="Need a rubber ring",
        )
        create_part_request_update(
            part_request=other_request,
            text="Part ordered",
        )

        results = list(
            PartRequestUpdate.objects.filter(part_request__machine=self.machine).search_for_machine(
                "flipper coil"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], update)

    def test_search_for_machine_matches_parent_requester_freetext_name(self):
        """Machine-scoped search should match parent's requester freetext name."""
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
            requested_by_name="Wandering Willie",
        )
        update = create_part_request_update(
            part_request=part_request,
            text="Part ordered",
        )
        other_request = create_part_request(machine=self.machine, text="Need a bulb")
        create_part_request_update(part_request=other_request, text="Ordered")

        results = list(
            PartRequestUpdate.objects.filter(part_request__machine=self.machine).search_for_machine(
                "Wandering"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], update)

    def test_search_for_machine_matches_parent_requester_username(self):
        """Machine-scoped search should match parent's requester username."""
        requester = create_maintainer_user(
            username="needsparts",
            first_name="",
            last_name="",
        )
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
            requested_by=requester.maintainer,
        )
        update = create_part_request_update(
            part_request=part_request,
            text="Part ordered",
        )
        other_request = create_part_request(machine=self.machine, text="Need a bulb")
        create_part_request_update(part_request=other_request, text="Ordered")

        results = list(
            PartRequestUpdate.objects.filter(part_request__machine=self.machine).search_for_machine(
                "needsparts"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], update)

    def test_search_for_machine_matches_parent_requester_first_name(self):
        """Machine-scoped search should match parent's requester first name."""
        requester = create_maintainer_user(
            username="user1",
            first_name="Wanda",
            last_name="",
        )
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
            requested_by=requester.maintainer,
        )
        update = create_part_request_update(
            part_request=part_request,
            text="Part ordered",
        )
        other_request = create_part_request(machine=self.machine, text="Need a bulb")
        create_part_request_update(part_request=other_request, text="Ordered")

        results = list(
            PartRequestUpdate.objects.filter(part_request__machine=self.machine).search_for_machine(
                "Wanda"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], update)

    def test_search_for_machine_matches_parent_requester_last_name(self):
        """Machine-scoped search should match parent's requester last name."""
        requester = create_maintainer_user(
            username="user1",
            first_name="",
            last_name="Techworthy",
        )
        part_request = create_part_request(
            machine=self.machine,
            text="Need a coil",
            requested_by=requester.maintainer,
        )
        update = create_part_request_update(
            part_request=part_request,
            text="Part ordered",
        )
        other_request = create_part_request(machine=self.machine, text="Need a bulb")
        create_part_request_update(part_request=other_request, text="Ordered")

        results = list(
            PartRequestUpdate.objects.filter(part_request__machine=self.machine).search_for_machine(
                "Techworthy"
            )
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], update)
