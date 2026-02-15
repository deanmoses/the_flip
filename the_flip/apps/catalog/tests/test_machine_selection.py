"""Tests for machine selection helpers (validators and view helpers)."""

from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase, tag

from the_flip.apps.catalog.validators import clean_machine_slug
from the_flip.apps.catalog.view_helpers import resolve_selected_machine
from the_flip.apps.core.test_utils import create_machine


@tag("forms")
class TestCleanMachineSlug(TestCase):
    """Tests for the clean_machine_slug form validator."""

    def test_valid_slug_returns_slug(self):
        """Valid machine slug is returned as-is."""
        machine = create_machine()
        result = clean_machine_slug({"machine_slug": machine.slug})
        self.assertEqual(result, machine.slug)

    def test_empty_slug_returns_empty_string(self):
        """Empty slug returns empty string (field is optional)."""
        self.assertEqual(clean_machine_slug({"machine_slug": ""}), "")
        self.assertEqual(clean_machine_slug({"machine_slug": "  "}), "")
        self.assertEqual(clean_machine_slug({"machine_slug": None}), "")
        self.assertEqual(clean_machine_slug({}), "")

    def test_nonexistent_slug_raises_validation_error(self):
        """Nonexistent slug raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            clean_machine_slug({"machine_slug": "no-such-machine"})
        self.assertIn("Select a machine.", ctx.exception.messages)


@tag("views")
class TestResolveSelectedMachine(TestCase):
    """Tests for the resolve_selected_machine view helper."""

    def setUp(self):
        self.factory = RequestFactory()
        self.machine = create_machine()

    def test_returns_machine_when_provided(self):
        """URL-derived machine is returned regardless of POST data."""
        request = self.factory.post("/", {"machine_slug": "other-slug"})
        result = resolve_selected_machine(request, self.machine)
        self.assertEqual(result, self.machine)

    def test_returns_machine_from_post_slug(self):
        """Looks up machine from POST slug when no URL-derived machine."""
        request = self.factory.post("/", {"machine_slug": self.machine.slug})
        result = resolve_selected_machine(request, None)
        self.assertEqual(result, self.machine)

    def test_returns_none_on_get_with_no_machine(self):
        """Returns None for GET requests with no URL-derived machine."""
        request = self.factory.get("/")
        result = resolve_selected_machine(request, None)
        self.assertIsNone(result)

    def test_returns_none_when_post_slug_not_found(self):
        """Returns None when POST slug doesn't match any machine."""
        request = self.factory.post("/", {"machine_slug": "no-such-machine"})
        result = resolve_selected_machine(request, None)
        self.assertIsNone(result)
