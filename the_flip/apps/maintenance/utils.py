"""
Utilities for handling maintenance media uploads.

DEPRECATED: This module is a compatibility shim. Import from the_flip.apps.core.models instead.
"""

from the_flip.apps.core.models import (
    MAX_IMAGE_DIMENSION,
    THUMB_IMAGE_DIMENSION,
    resize_image_file,
)

__all__ = ["MAX_IMAGE_DIMENSION", "THUMB_IMAGE_DIMENSION", "resize_image_file"]
