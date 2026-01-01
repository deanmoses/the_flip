"""Tests for parts forms."""

from django.test import TestCase, tag

from the_flip.apps.core.test_utils import (
    TestDataMixin,
    create_part_request,
    create_part_request_update,
)
from the_flip.apps.parts.forms import (
    PartRequestEditForm,
    PartRequestUpdateEditForm,
)


@tag("forms")
class PartRequestEditFormTests(TestDataMixin, TestCase):
    """Tests for PartRequestEditForm validation.

    Note: Future date validation is tested in test_part_request_edit.py
    as a view test, since validation happens after timezone conversion
    in form_valid().
    """

    def setUp(self):
        super().setUp()
        self.part_request = create_part_request(
            text="Test part request",
            requested_by=self.maintainer,
        )

    def test_occurred_at_is_required(self):
        """Form requires occurred_at field."""
        form = PartRequestEditForm(
            data={"occurred_at": ""},
            instance=self.part_request,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("occurred_at", form.errors)


@tag("forms")
class PartRequestUpdateEditFormTests(TestDataMixin, TestCase):
    """Tests for PartRequestUpdateEditForm validation.

    Note: Future date validation is tested in test_part_request_edit.py
    as a view test, since validation happens after timezone conversion
    in form_valid().
    """

    def setUp(self):
        super().setUp()
        self.part_request = create_part_request(
            text="Test part request",
            requested_by=self.maintainer,
        )
        self.update = create_part_request_update(
            part_request=self.part_request,
            posted_by=self.maintainer,
            text="Test update",
        )

    def test_occurred_at_is_required(self):
        """Form requires occurred_at field."""
        form = PartRequestUpdateEditForm(
            data={"occurred_at": ""},
            instance=self.update,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("occurred_at", form.errors)
