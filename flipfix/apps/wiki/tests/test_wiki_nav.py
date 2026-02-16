"""Tests for wiki navigation (path parsing and nav tree building)."""

from django.http import Http404
from django.test import TestCase, tag

from flipfix.apps.wiki.models import WikiPage, WikiPageTag, WikiTagOrder
from flipfix.apps.wiki.templatetags.wiki_tags import deslugify
from flipfix.apps.wiki.views import build_nav_tree, parse_wiki_path


@tag("views")
class ParseWikiPathTests(TestCase):
    """Tests for parse_wiki_path URL parsing."""

    def test_single_segment_is_untagged(self):
        """Single path segment is slug with empty tag."""
        result_tag, slug = parse_wiki_path("overview")
        self.assertEqual(result_tag, "")
        self.assertEqual(slug, "overview")

    def test_two_segments(self):
        """Two segments: first is tag, second is slug."""
        result_tag, slug = parse_wiki_path("machines/overview")
        self.assertEqual(result_tag, "machines")
        self.assertEqual(slug, "overview")

    def test_nested_tag(self):
        """Multiple segments before slug form nested tag."""
        result_tag, slug = parse_wiki_path("machines/blackout/system-6")
        self.assertEqual(result_tag, "machines/blackout")
        self.assertEqual(slug, "system-6")

    def test_trailing_slash_stripped(self):
        """Trailing slash is stripped."""
        result_tag, slug = parse_wiki_path("machines/overview/")
        self.assertEqual(result_tag, "machines")
        self.assertEqual(slug, "overview")

    def test_empty_path_raises_404(self):
        """Empty path raises Http404."""
        with self.assertRaises(Http404):
            parse_wiki_path("")


@tag("views")
class BuildNavTreeTests(TestCase):
    """Tests for build_nav_tree navigation tree builder."""

    def test_empty_tree(self):
        """Empty database returns empty tree."""
        tree = build_nav_tree()

        self.assertEqual(tree["pages"], [])
        self.assertEqual(tree["children"], {})

    def test_untagged_pages_at_root(self):
        """Untagged pages appear at root level."""
        # Signal auto-creates untagged sentinel
        WikiPage.objects.create(title="Root", slug="root")

        tree = build_nav_tree()

        self.assertEqual(len(tree["pages"]), 1)
        self.assertEqual(tree["pages"][0]["page"].title, "Root")

    def test_tagged_pages_in_children(self):
        """Tagged pages appear under their tag."""
        page = WikiPage.objects.create(title="Nested", slug="nested")
        WikiPageTag.objects.create(page=page, tag="docs", slug="nested")

        tree = build_nav_tree()

        self.assertEqual(len(tree["pages"]), 0)
        self.assertIn("docs", tree["children"])
        self.assertEqual(len(tree["children"]["docs"]["pages"]), 1)

    def test_nested_tags(self):
        """Nested tags create nested tree structure."""
        page = WikiPage.objects.create(title="Deep", slug="deep")
        WikiPageTag.objects.create(page=page, tag="machines/blackout", slug="deep")

        tree = build_nav_tree()

        self.assertIn("machines", tree["children"])
        self.assertIn("blackout", tree["children"]["machines"]["children"])
        self.assertEqual(
            tree["children"]["machines"]["children"]["blackout"]["pages"][0]["page"].title,
            "Deep",
        )

    def test_pages_sorted_by_order_then_title(self):
        """Pages sort by order (nulls last), then by title."""
        page1 = WikiPage.objects.create(title="Beta", slug="beta")
        page2 = WikiPage.objects.create(title="Alpha", slug="alpha")
        page3 = WikiPage.objects.create(title="Gamma", slug="gamma")

        WikiPageTag.objects.create(page=page1, tag="docs", slug="beta", order=None)
        WikiPageTag.objects.create(page=page2, tag="docs", slug="alpha", order=None)
        WikiPageTag.objects.create(page=page3, tag="docs", slug="gamma", order=1)

        tree = build_nav_tree()
        pages = tree["children"]["docs"]["pages"]

        # Gamma (ordered) first, then Alpha, Beta (alphabetical)
        self.assertEqual(pages[0]["page"].title, "Gamma")
        self.assertEqual(pages[1]["page"].title, "Alpha")
        self.assertEqual(pages[2]["page"].title, "Beta")

    def test_children_sorted_alphabetically_by_default(self):
        """Sibling tag nodes sort alphabetically when no explicit order."""
        # Create pages in non-alphabetical tags
        for tag_name in ["zebra", "alpha", "middle"]:
            page = WikiPage.objects.create(title=f"Page in {tag_name}", slug=f"page-{tag_name}")
            WikiPageTag.objects.create(page=page, tag=tag_name, slug=f"page-{tag_name}")

        tree = build_nav_tree()
        child_keys = list(tree["children"].keys())

        self.assertEqual(child_keys, ["alpha", "middle", "zebra"])

    def test_children_sorted_by_explicit_order(self):
        """Sibling tag nodes with WikiTagOrder sort by order, then alphabetically."""
        for tag_name in ["zebra", "alpha", "middle"]:
            page = WikiPage.objects.create(title=f"Page in {tag_name}", slug=f"page-{tag_name}")
            WikiPageTag.objects.create(page=page, tag=tag_name, slug=f"page-{tag_name}")

        # Explicitly order "zebra" first
        WikiTagOrder.objects.create(tag="zebra", order=1)

        tree = build_nav_tree()
        child_keys = list(tree["children"].keys())

        # zebra (ordered=1) first, then alpha, middle (alphabetical)
        self.assertEqual(child_keys, ["zebra", "alpha", "middle"])

    def test_nested_children_sorted_by_explicit_order(self):
        """Nested tag children with WikiTagOrder are sorted by order."""
        for sub in ["alpha", "zebra"]:
            page = WikiPage.objects.create(title=f"Page in {sub}", slug=f"page-{sub}")
            WikiPageTag.objects.create(page=page, tag=f"machines/{sub}", slug=f"page-{sub}")

        # Explicitly order "zebra" before "alpha"
        WikiTagOrder.objects.create(tag="machines/zebra", order=1)

        tree = build_nav_tree()
        nested_keys = list(tree["children"]["machines"]["children"].keys())

        self.assertEqual(nested_keys, ["zebra", "alpha"])


class DeslugifyFilterTests(TestCase):
    """Tests for the deslugify template filter."""

    def test_replaces_hyphens_with_spaces(self):
        self.assertEqual(deslugify("using-flipfix"), "Using Flipfix")

    def test_single_word(self):
        self.assertEqual(deslugify("procedures"), "Procedures")

    def test_multiple_hyphens(self):
        self.assertEqual(deslugify("one-two-three"), "One Two Three")
