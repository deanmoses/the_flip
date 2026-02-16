"""Tests for [[type:ref]] link rendering in markdown (non-page types)."""

from django.test import TestCase, tag

from flipfix.apps.catalog.models import MachineInstance, MachineModel
from flipfix.apps.core.markdown_links import render_all_links
from flipfix.apps.core.templatetags.markdown_tags import render_markdown
from flipfix.apps.maintenance.models import LogEntry, ProblemReport
from flipfix.apps.parts.models import PartRequest, PartRequestUpdate


@tag("views")
class MachineLinkRenderingTests(TestCase):
    """Tests for [[machine:id:N]] link rendering."""

    def test_machine_link_renders_as_anchor(self):
        """[[machine:id:N]] renders as a link with machine name."""
        model = MachineModel.objects.create(name="Black Knight", slug="black-knight")
        machine = MachineInstance.objects.create(model=model, slug="blackout", name="Blackout")

        result = render_markdown(f"See [[machine:id:{machine.pk}]] for details.")

        self.assertIn("<a href=", result)
        self.assertIn("Blackout", result)
        self.assertIn("/machines/blackout", result)

    def test_machine_link_deleted_machine(self):
        """[[machine:id:N]] for deleted machine shows [broken link] text."""
        result = render_markdown("See [[machine:id:99999]] for info.")

        self.assertIn("[broken link]", result)
        self.assertIn("<em>", result)

    def test_multiple_machine_links(self):
        """Multiple [[machine:id:N]] links in same text all render."""
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        machine1 = MachineInstance.objects.create(model=model, slug="machine-1", name="Machine One")
        machine2 = MachineInstance.objects.create(model=model, slug="machine-2", name="Machine Two")

        result = render_markdown(
            f"See [[machine:id:{machine1.pk}]] and [[machine:id:{machine2.pk}]]."
        )

        self.assertIn("Machine One", result)
        self.assertIn("Machine Two", result)


@tag("views")
class ModelLinkRenderingTests(TestCase):
    """Tests for [[model:id:N]] link rendering."""

    def test_model_link_renders_as_anchor(self):
        """[[model:id:N]] renders as a link with model name."""
        model = MachineModel.objects.create(name="Black Knight", slug="black-knight")

        result = render_markdown(f"See [[model:id:{model.pk}]] for details.")

        self.assertIn("<a href=", result)
        self.assertIn("Black Knight", result)
        self.assertIn("/models/black-knight", result)

    def test_model_link_deleted_model(self):
        """[[model:id:N]] for deleted model shows [broken link] text."""
        result = render_markdown("See [[model:id:99999]] for info.")

        self.assertIn("[broken link]", result)
        self.assertIn("<em>", result)

    def test_multiple_model_links(self):
        """Multiple [[model:id:N]] links in same text all render."""
        model1 = MachineModel.objects.create(name="Model One", slug="model-1")
        model2 = MachineModel.objects.create(name="Model Two", slug="model-2")

        result = render_markdown(f"See [[model:id:{model1.pk}]] and [[model:id:{model2.pk}]].")

        self.assertIn("Model One", result)
        self.assertIn("Model Two", result)


@tag("views")
class ProblemLinkRenderingTests(TestCase):
    """Tests for [[problem:N]] link rendering."""

    @classmethod
    def setUpTestData(cls):
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        cls.machine = MachineInstance.objects.create(
            model=model, slug="test-machine", name="Test Machine"
        )

    def test_problem_link_includes_description_preview(self):
        """[[problem:N]] renders with truncated description in link text."""
        pr = ProblemReport.objects.create(
            machine=self.machine, description="Flipper stuck on left side"
        )

        result = render_markdown(f"See [[problem:{pr.pk}]].")

        self.assertIn("<a href=", result)
        self.assertIn(f"Problem #{pr.pk}", result)
        self.assertIn("Flipper stuck", result)

    def test_problem_link_truncates_long_description(self):
        """Long descriptions are truncated with ellipsis."""
        pr = ProblemReport.objects.create(
            machine=self.machine,
            description="This is a very long description that should be truncated at thirty characters",
        )

        result = render_markdown(f"See [[problem:{pr.pk}]].")

        # Markdown renderer may convert "..." to unicode ellipsis
        self.assertTrue("..." in result or "\u2026" in result)
        self.assertNotIn("thirty characters", result)

    def test_problem_link_empty_description(self):
        """Problem with empty description shows just the ID."""
        pr = ProblemReport.objects.create(machine=self.machine, description="")

        result = render_markdown(f"See [[problem:{pr.pk}]].")

        self.assertIn(f"Problem #{pr.pk}", result)
        self.assertIn("<a href=", result)

    def test_problem_link_deleted(self):
        """[[problem:N]] for deleted problem shows [broken link]."""
        result = render_markdown("See [[problem:99999]].")

        self.assertIn("[broken link]", result)

    def test_problem_link_strips_brackets_from_preview(self):
        """Description containing brackets doesn't break markdown link syntax."""
        pr = ProblemReport.objects.create(
            machine=self.machine, description="Ball stuck [behind ramp]"
        )

        result = render_markdown(f"See [[problem:{pr.pk}]].")

        # Should render as a valid link, not broken markdown
        self.assertIn("<a href=", result)
        self.assertIn("behind ramp", result)


@tag("views")
class LogLinkRenderingTests(TestCase):
    """Tests for [[log:N]] link rendering."""

    @classmethod
    def setUpTestData(cls):
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        cls.machine = MachineInstance.objects.create(
            model=model, slug="test-machine", name="Test Machine"
        )

    def test_log_link_includes_text_preview(self):
        """[[log:N]] renders with truncated text in link text."""
        le = LogEntry.objects.create(machine=self.machine, text="Replaced flipper rubber")

        result = render_markdown(f"See [[log:{le.pk}]].")

        self.assertIn("<a href=", result)
        self.assertIn(f"Log #{le.pk}", result)
        self.assertIn("Replaced flipper", result)

    def test_log_link_deleted(self):
        """[[log:N]] for deleted log shows [broken link]."""
        result = render_markdown("See [[log:99999]].")

        self.assertIn("[broken link]", result)


@tag("views")
class PartRequestLinkRenderingTests(TestCase):
    """Tests for [[partrequest:N]] link rendering."""

    def test_partrequest_link_includes_text_preview(self):
        """[[partrequest:N]] renders with truncated text in link text."""
        pr = PartRequest.objects.create(text="Need new flipper bat for left side")

        result = render_markdown(f"See [[partrequest:{pr.pk}]].")

        self.assertIn("<a href=", result)
        self.assertIn(f"Part Request #{pr.pk}", result)
        self.assertIn("Need new flipper", result)

    def test_partrequest_link_deleted(self):
        """[[partrequest:N]] for deleted part request shows [broken link]."""
        result = render_markdown("See [[partrequest:99999]].")

        self.assertIn("[broken link]", result)


@tag("views")
class PartRequestUpdateLinkRenderingTests(TestCase):
    """Tests for [[partrequestupdate:N]] link rendering."""

    def test_partrequestupdate_link_includes_text_preview(self):
        """[[partrequestupdate:N]] renders with text preview and parent ID."""
        pr = PartRequest.objects.create(text="Need parts")
        update = PartRequestUpdate.objects.create(
            part_request=pr, text="Ordered from supplier today"
        )

        result = render_markdown(f"See [[partrequestupdate:{update.pk}]].")

        self.assertIn("<a href=", result)
        self.assertIn(f"Update #{update.pk} on #{pr.pk}", result)
        self.assertIn("Ordered from supplier", result)

    def test_partrequestupdate_link_deleted(self):
        """[[partrequestupdate:N]] for deleted update shows [broken link]."""
        result = render_markdown("See [[partrequestupdate:99999]].")

        self.assertIn("[broken link]", result)


@tag("views")
class BaseUrlRenderingTests(TestCase):
    """Tests for render_all_links() with base_url parameter."""

    def test_base_url_produces_absolute_links(self):
        """render_all_links with base_url prepends it to link URLs."""
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        machine = MachineInstance.objects.create(model=model, slug="blackout", name="Blackout")

        result = render_all_links(
            f"See [[machine:id:{machine.pk}]].", base_url="https://example.com"
        )

        self.assertIn("[Blackout](https://example.com/machines/blackout/)", result)

    def test_default_base_url_produces_relative_links(self):
        """Default base_url produces relative URLs (existing behavior)."""
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        machine = MachineInstance.objects.create(model=model, slug="blackout", name="Blackout")

        result = render_all_links(f"See [[machine:id:{machine.pk}]].")

        self.assertIn("[Blackout](/machines/blackout/)", result)
        self.assertNotIn("https://", result)

    def test_base_url_with_id_based_link(self):
        """base_url works with ID-based link types."""
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        machine = MachineInstance.objects.create(model=model, slug="test-machine", name="Test")
        pr = ProblemReport.objects.create(machine=machine, description="Stuck flipper")

        result = render_all_links(f"See [[problem:{pr.pk}]].", base_url="https://example.com")

        self.assertIn("https://example.com/problem-reports/", result)

    def test_base_url_with_broken_link(self):
        """Broken links still render as *[broken link]* even with base_url."""
        result = render_all_links("See [[machine:id:99999]].", base_url="https://example.com")

        self.assertIn("*[broken link]*", result)


@tag("views")
class PlainTextRenderingTests(TestCase):
    """Tests for render_all_links() with plain_text parameter."""

    def test_plain_text_renders_label_only(self):
        """plain_text=True renders just the label with no link syntax."""
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        machine = MachineInstance.objects.create(model=model, slug="blackout", name="Blackout")

        result = render_all_links(f"See [[machine:id:{machine.pk}]].", plain_text=True)

        self.assertIn("See Blackout.", result)
        self.assertNotIn("[", result)
        self.assertNotIn("(", result)

    def test_plain_text_with_broken_link(self):
        """Broken links in plain_text mode render without markdown emphasis."""
        result = render_all_links("See [[machine:id:99999]].", plain_text=True)

        self.assertIn("[broken link]", result)
        self.assertNotIn("*", result)

    def test_plain_text_with_id_based_link(self):
        """plain_text works with ID-based link types."""
        model = MachineModel.objects.create(name="Test Model", slug="test-model")
        machine = MachineInstance.objects.create(model=model, slug="test-machine", name="Test")
        pr = ProblemReport.objects.create(machine=machine, description="Stuck flipper")

        result = render_all_links(f"See [[problem:{pr.pk}]].", plain_text=True)

        self.assertIn(f"Problem #{pr.pk}", result)
        self.assertNotIn("](/", result)
