"""Tests for wiki page link conversion and delete warnings."""

from django.test import TestCase, tag

from the_flip.apps.core.markdown_links import (
    convert_authoring_to_storage,
    convert_storage_to_authoring,
    sync_references,
)

from ..links import get_pages_linking_here
from ..models import WikiPage, WikiPageTag


@tag("views")
class PageAuthoringToStorageConversionTests(TestCase):
    """Tests for converting page authoring format to storage format."""

    def test_page_link_converts_to_id(self):
        """[[page:path]] converts to [[page:id:N]]."""
        page = WikiPage.objects.create(title="Test Page", slug="test-page")
        page_tag = WikiPageTag.objects.create(page=page, tag="docs", slug="test-page")

        content = "See [[page:docs/test-page]] for details."
        result = convert_authoring_to_storage(content)

        self.assertEqual(result, f"See [[page:id:{page_tag.pk}]] for details.")

    def test_page_link_untagged(self):
        """[[page:slug]] for untagged page converts correctly."""
        page = WikiPage.objects.create(title="Root Page", slug="root-page")
        page_tag = page.tags.first()  # Auto-created sentinel

        content = "See [[page:root-page]]."
        result = convert_authoring_to_storage(content)

        self.assertEqual(result, f"See [[page:id:{page_tag.pk}]].")

    def test_page_link_nested_tag(self):
        """[[page:nested/path/slug]] converts correctly."""
        page = WikiPage.objects.create(title="Nested", slug="nested")
        page_tag = WikiPageTag.objects.create(page=page, tag="machines/blackout", slug="nested")

        content = "See [[page:machines/blackout/nested]]."
        result = convert_authoring_to_storage(content)

        self.assertEqual(result, f"See [[page:id:{page_tag.pk}]].")

    def test_broken_page_link_raises_error(self):
        """[[page:nonexistent]] raises ValidationError."""
        from django.core.exceptions import ValidationError

        content = "See [[page:nonexistent]]."

        with self.assertRaises(ValidationError) as ctx:
            convert_authoring_to_storage(content)

        self.assertIn("Page not found", str(ctx.exception))


@tag("views")
class PageStorageToAuthoringConversionTests(TestCase):
    """Tests for converting page storage format to authoring format."""

    def test_page_link_converts_to_path(self):
        """[[page:id:N]] converts to [[page:path]]."""
        page = WikiPage.objects.create(title="Test Page", slug="test-page")
        page_tag = WikiPageTag.objects.create(page=page, tag="docs", slug="test-page")

        content = f"See [[page:id:{page_tag.pk}]] for details."
        result = convert_storage_to_authoring(content)

        self.assertEqual(result, "See [[page:docs/test-page]] for details.")

    def test_page_link_untagged(self):
        """[[page:id:N]] for untagged page shows just slug."""
        page = WikiPage.objects.create(title="Root Page", slug="root-page")
        page_tag = page.tags.first()  # Untagged sentinel

        content = f"See [[page:id:{page_tag.pk}]]."
        result = convert_storage_to_authoring(content)

        self.assertEqual(result, "See [[page:root-page]].")


@tag("views")
class DeleteWarningTests(TestCase):
    """Tests for delete warning functionality (warn-and-allow, not blocking)."""

    def test_page_with_no_references_has_no_linking_pages(self):
        """Page without incoming references has no linking pages."""
        page = WikiPage.objects.create(title="Lonely Page", slug="lonely")

        linking = get_pages_linking_here(page)

        self.assertEqual(linking, [])

    def test_page_with_references_shows_linking_pages(self):
        """Page with incoming references lists the linking pages."""
        target = WikiPage.objects.create(title="Target", slug="target")
        target_tag = target.tags.first()

        source = WikiPage.objects.create(title="Source", slug="source", content="")
        source.content = f"See [[page:id:{target_tag.pk}]]."
        source.save()
        sync_references(source, source.content)

        linking = get_pages_linking_here(target)

        self.assertEqual(len(linking), 1)
        self.assertEqual(linking[0], source)

    def test_get_pages_linking_here_returns_all_referencing_pages(self):
        """get_pages_linking_here returns all pages that reference the target."""
        target = WikiPage.objects.create(title="Target", slug="target")
        target_tag = target.tags.first()

        source1 = WikiPage.objects.create(title="Source 1", slug="source-1", content="")
        source1.content = f"See [[page:id:{target_tag.pk}]]."
        source1.save()
        sync_references(source1, source1.content)

        source2 = WikiPage.objects.create(title="Source 2", slug="source-2", content="")
        source2.content = f"Also see [[page:id:{target_tag.pk}]]."
        source2.save()
        sync_references(source2, source2.content)

        linking = get_pages_linking_here(target)

        self.assertEqual(len(linking), 2)
        self.assertIn(source1, linking)
        self.assertIn(source2, linking)

    def test_self_reference_excluded(self):
        """A page referencing itself is excluded from linking pages."""
        page = WikiPage.objects.create(title="Self Referencing", slug="self-ref")
        page_tag = page.tags.first()

        page.content = f"I link to myself: [[page:id:{page_tag.pk}]]."
        page.save()
        sync_references(page, page.content)

        linking = get_pages_linking_here(page)

        self.assertEqual(linking, [])

    def test_linking_pages_sorted_by_title(self):
        """Linking pages are returned sorted alphabetically by title."""
        target = WikiPage.objects.create(title="Target", slug="target")
        target_tag = target.tags.first()

        # Create pages in non-alphabetical order
        source_z = WikiPage.objects.create(title="Zebra", slug="zebra", content="")
        source_z.content = f"[[page:id:{target_tag.pk}]]"
        source_z.save()
        sync_references(source_z, source_z.content)

        source_a = WikiPage.objects.create(title="Apple", slug="apple", content="")
        source_a.content = f"[[page:id:{target_tag.pk}]]"
        source_a.save()
        sync_references(source_a, source_a.content)

        source_m = WikiPage.objects.create(title="Mango", slug="mango", content="")
        source_m.content = f"[[page:id:{target_tag.pk}]]"
        source_m.save()
        sync_references(source_m, source_m.content)

        linking = get_pages_linking_here(target)

        self.assertEqual([p.title for p in linking], ["Apple", "Mango", "Zebra"])
