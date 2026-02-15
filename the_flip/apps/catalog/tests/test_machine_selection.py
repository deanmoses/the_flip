"""Tests for machine selection helpers (validators and view helpers)."""

from django.core.exceptions import ValidationError
from django.test import TestCase, tag

from the_flip.apps.catalog.validators import clean_machine_slug
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
