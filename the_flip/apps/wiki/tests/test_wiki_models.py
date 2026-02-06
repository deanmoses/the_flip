"""Tests for Wiki models."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, tag

from the_flip.apps.wiki.models import UNTAGGED_SENTINEL, WikiPage, WikiPageTag, WikiTagOrder


@tag("models")
class WikiPageStrTests(TestCase):
    """Tests for WikiPage.__str__."""

    def test_str_returns_title(self):
        """__str__ returns the page title."""
        page = WikiPage.objects.create(title="Test Page", slug="test-page")
        self.assertEqual(str(page), "Test Page")


@tag("models")
class WikiPageSlugSyncTests(TestCase):
    """Tests for WikiPage.save() slug syncing to WikiPageTag."""

    def test_slug_change_syncs_to_tags(self):
        """Changing a page's slug updates all its WikiPageTag.slug values."""
        page = WikiPage.objects.create(title="Original", slug="original")
        WikiPageTag.objects.create(page=page, tag="machines", slug="original")
        WikiPageTag.objects.create(page=page, tag="guides", slug="original")

        page.slug = "renamed"
        page.save()

        # Both tags should have updated slug
        slugs = list(page.tags.values_list("slug", flat=True))
        self.assertEqual(slugs, ["renamed", "renamed"])

    def test_new_page_gets_untagged_sentinel(self):
        """Creating a new page auto-creates an untagged sentinel tag."""
        page = WikiPage.objects.create(title="New Page", slug="new-page")

        # Signal should have created one tag with empty string
        self.assertEqual(page.tags.count(), 1)
        tag = page.tags.first()
        self.assertEqual(tag.tag, UNTAGGED_SENTINEL)
        self.assertEqual(tag.slug, "new-page")

    def test_adding_tag_removes_untagged_sentinel(self):
        """Adding a non-empty tag removes the auto-created sentinel."""
        page = WikiPage.objects.create(title="Page", slug="page")

        # Initially has the untagged sentinel
        self.assertEqual(page.tags.count(), 1)
        self.assertEqual(page.tags.first().tag, UNTAGGED_SENTINEL)

        # Add a real tag
        WikiPageTag.objects.create(page=page, tag="docs", slug="page")

        # Sentinel should be removed, only "docs" tag remains
        self.assertEqual(page.tags.count(), 1)
        self.assertEqual(page.tags.first().tag, "docs")

    def test_slug_unchanged_does_not_query_tags(self):
        """Saving without changing slug doesn't update tags."""
        page = WikiPage.objects.create(title="Original", slug="original")
        WikiPageTag.objects.create(page=page, tag="machines", slug="original")

        # Change title but not slug
        page.title = "Updated Title"
        page.save()

        # Slug should still be original
        tag_record = page.tags.first()
        self.assertEqual(tag_record.slug, "original")


@tag("models")
class WikiPageSlugCollisionTests(TestCase):
    """Tests for WikiPage.save() collision detection."""

    def test_slug_collision_raises_validation_error(self):
        """Changing slug to one that exists in same tag raises ValidationError."""
        page1 = WikiPage.objects.create(title="Page 1", slug="page-one")
        page2 = WikiPage.objects.create(title="Page 2", slug="page-two")

        WikiPageTag.objects.create(page=page1, tag="machines", slug="page-one")
        WikiPageTag.objects.create(page=page2, tag="machines", slug="page-two")

        # Try to rename page2's slug to match page1's
        page2.slug = "page-one"

        with self.assertRaises(ValidationError) as context:
            page2.save()

        self.assertIn("page-one", str(context.exception))

    def test_slug_collision_across_multiple_tags(self):
        """Collision is detected if slug conflicts in ANY of the page's tags."""
        page1 = WikiPage.objects.create(title="Page 1", slug="page-one")
        page2 = WikiPage.objects.create(title="Page 2", slug="page-two")

        # page1 only in "machines"
        WikiPageTag.objects.create(page=page1, tag="machines", slug="page-one")

        # page2 in "guides" and "machines"
        WikiPageTag.objects.create(page=page2, tag="guides", slug="page-two")
        WikiPageTag.objects.create(page=page2, tag="machines", slug="page-two")

        # page2 renaming to "page-one" should fail (conflicts in "machines")
        page2.slug = "page-one"

        with self.assertRaises(ValidationError):
            page2.save()

    def test_no_collision_in_different_tags(self):
        """Same slug is allowed in different tags."""
        page1 = WikiPage.objects.create(title="Page 1", slug="overview")
        page2 = WikiPage.objects.create(title="Page 2", slug="overview-temp")

        WikiPageTag.objects.create(page=page1, tag="machines", slug="overview")
        WikiPageTag.objects.create(page=page2, tag="guides", slug="overview-temp")

        # page2 can use "overview" since it's only in "guides"
        page2.slug = "overview"
        page2.save()  # Should not raise

        tag_record = page2.tags.first()
        self.assertEqual(tag_record.slug, "overview")


@tag("models")
class WikiPageTagStrTests(TestCase):
    """Tests for WikiPageTag.__str__."""

    def test_str_with_tag_returns_full_path(self):
        """__str__ returns 'tag/slug' when tag is set."""
        page = WikiPage.objects.create(title="Test", slug="test-page")
        tag_record = WikiPageTag.objects.create(
            page=page, tag="machines/blackout", slug="test-page"
        )
        self.assertEqual(str(tag_record), "machines/blackout/test-page")

    def test_str_without_tag_returns_slug(self):
        """__str__ returns just slug when tag is empty (untagged page)."""
        page = WikiPage.objects.create(title="Test", slug="test-page")
        # Signal auto-creates untagged sentinel
        tag_record = page.tags.first()
        self.assertEqual(str(tag_record), "test-page")


@tag("models")
class WikiPageTagNormalizationTests(TestCase):
    """Tests for WikiPageTag.save() tag normalization."""

    def test_tag_normalized_to_lowercase(self):
        """Tags are normalized to lowercase on save."""
        page = WikiPage.objects.create(title="Test", slug="test")
        tag_record = WikiPageTag.objects.create(page=page, tag="Machines", slug="test")

        self.assertEqual(tag_record.tag, "machines")

    def test_tag_path_segments_normalized(self):
        """Each segment of a tag path is slugified."""
        page = WikiPage.objects.create(title="Test", slug="test")
        tag_record = WikiPageTag.objects.create(page=page, tag="Machines/My Blackout", slug="test")

        self.assertEqual(tag_record.tag, "machines/my-blackout")

    def test_mixed_case_tag_path_normalized(self):
        """Mixed case tag paths are normalized consistently."""
        page = WikiPage.objects.create(title="Test", slug="test")
        tag_record = WikiPageTag.objects.create(page=page, tag="GUIDES/How To/REPAIR", slug="test")

        self.assertEqual(tag_record.tag, "guides/how-to/repair")

    def test_empty_tag_not_modified(self):
        """Empty tag (untagged sentinel) is preserved."""
        page = WikiPage.objects.create(title="Test", slug="test")
        # Signal creates untagged sentinel
        tag_record = page.tags.first()

        self.assertEqual(tag_record.tag, UNTAGGED_SENTINEL)


@tag("models")
class WikiPageTagConstraintTests(TestCase):
    """Tests for WikiPageTag unique constraints."""

    def test_unique_page_tag_constraint(self):
        """Cannot add same tag to a page twice."""
        page = WikiPage.objects.create(title="Test", slug="test")
        WikiPageTag.objects.create(page=page, tag="machines", slug="test")

        with self.assertRaises(IntegrityError):
            WikiPageTag.objects.create(page=page, tag="machines", slug="test")

    def test_unique_tag_slug_constraint(self):
        """Cannot have two pages with same slug under same tag."""
        page1 = WikiPage.objects.create(title="Page 1", slug="same-slug")
        page2 = WikiPage.objects.create(title="Page 2", slug="same-slug-2")

        WikiPageTag.objects.create(page=page1, tag="machines", slug="same-slug")

        with self.assertRaises(IntegrityError):
            WikiPageTag.objects.create(page=page2, tag="machines", slug="same-slug")

    def test_same_slug_different_tags_allowed(self):
        """Same slug under different tags is allowed."""
        page1 = WikiPage.objects.create(title="Page 1", slug="overview")
        page2 = WikiPage.objects.create(title="Page 2", slug="overview-2")

        WikiPageTag.objects.create(page=page1, tag="machines", slug="overview")
        # Different tag, same slug should work
        tag2 = WikiPageTag.objects.create(page=page2, tag="guides", slug="overview")

        self.assertEqual(tag2.slug, "overview")

    def test_untagged_pages_enforce_slug_uniqueness(self):
        """Two untagged pages cannot have same slug (auto-created sentinel enforces this)."""
        # First page gets untagged sentinel with slug="same-slug"
        WikiPage.objects.create(title="Page 1", slug="same-slug")

        # Second page with same slug will fail when signal tries to create sentinel
        with self.assertRaises(IntegrityError):
            WikiPage.objects.create(title="Page 2", slug="same-slug")


@tag("models")
class WikiPageTagOrderingTests(TestCase):
    """Tests for WikiPageTag ordering (order nulls last, then by title)."""

    def test_ordered_before_unordered(self):
        """Pages with explicit order appear before those without."""
        page1 = WikiPage.objects.create(title="Alpha", slug="alpha")
        page2 = WikiPage.objects.create(title="Beta", slug="beta")
        page3 = WikiPage.objects.create(title="Gamma", slug="gamma")

        # Gamma has order, Alpha and Beta don't
        WikiPageTag.objects.create(page=page1, tag="docs", slug="alpha", order=None)
        WikiPageTag.objects.create(page=page2, tag="docs", slug="beta", order=None)
        WikiPageTag.objects.create(page=page3, tag="docs", slug="gamma", order=1)

        tags = list(WikiPageTag.objects.filter(tag="docs"))
        # Gamma (ordered) first, then Alpha/Beta by title
        self.assertEqual(tags[0].page, page3)  # Gamma, order=1
        self.assertEqual(tags[1].page, page1)  # Alpha (alphabetical)
        self.assertEqual(tags[2].page, page2)  # Beta (alphabetical)

    def test_ordered_pages_sort_by_order(self):
        """Pages with explicit order sort by that order."""
        page1 = WikiPage.objects.create(title="First", slug="first")
        page2 = WikiPage.objects.create(title="Second", slug="second")
        page3 = WikiPage.objects.create(title="Third", slug="third")

        WikiPageTag.objects.create(page=page1, tag="docs", slug="first", order=3)
        WikiPageTag.objects.create(page=page2, tag="docs", slug="second", order=1)
        WikiPageTag.objects.create(page=page3, tag="docs", slug="third", order=2)

        tags = list(WikiPageTag.objects.filter(tag="docs"))
        self.assertEqual([t.page for t in tags], [page2, page3, page1])


@tag("models")
class WikiTagOrderStrTests(TestCase):
    """Tests for WikiTagOrder.__str__."""

    def test_str_returns_tag_with_order(self):
        """__str__ returns 'tag (order=N)' format."""
        tag_order = WikiTagOrder.objects.create(tag="machines/blackout", order=5)
        self.assertEqual(str(tag_order), "machines/blackout (order=5)")


@tag("models")
class WikiTagOrderOrderingTests(TestCase):
    """Tests for WikiTagOrder default ordering."""

    def test_ordered_by_order_field(self):
        """WikiTagOrder entries are sorted by order field."""
        WikiTagOrder.objects.create(tag="third", order=30)
        WikiTagOrder.objects.create(tag="first", order=10)
        WikiTagOrder.objects.create(tag="second", order=20)

        tags = list(WikiTagOrder.objects.values_list("tag", flat=True))
        self.assertEqual(tags, ["first", "second", "third"])
