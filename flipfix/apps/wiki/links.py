"""Wiki-specific link utilities.

Shared link conversion and reference syncing code lives in
flipfix.apps.core.markdown_links. This module contains only
wiki-specific functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import WikiPage


def get_pages_linking_here(page: WikiPage) -> list[WikiPage]:
    """Return wiki pages that link to this page (for delete warning UI).

    Queries the RecordReference table for wiki pages (not other source
    types) that reference any of this page's WikiPageTags.

    Args:
        page: The WikiPage to check for incoming links

    Returns:
        List of WikiPages that link to this page, ordered by title
    """
    from django.contrib.contenttypes.models import ContentType

    from flipfix.apps.core.models import RecordReference

    from .models import WikiPage as WikiPageModel
    from .models import WikiPageTag

    page_tag_ids = list(page.tags.values_list("pk", flat=True))
    if not page_tag_ids:
        return []

    page_ct = ContentType.objects.get_for_model(WikiPageModel)
    page_tag_ct = ContentType.objects.get_for_model(WikiPageTag)

    # Find wiki pages (not other source types) that reference this page's tags
    referencing_page_ids = (
        RecordReference.objects.filter(
            source_type=page_ct,
            target_type=page_tag_ct,
            target_id__in=page_tag_ids,
        )
        .exclude(source_id=page.pk)
        .values_list("source_id", flat=True)
    )

    return list(
        WikiPageModel.objects.filter(pk__in=referencing_page_ids).distinct().order_by("title")
    )
