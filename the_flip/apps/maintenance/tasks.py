"""
Background tasks for maintenance media.

DEPRECATED: This module is a compatibility shim. Import from the_flip.apps.core.tasks instead.
"""

from the_flip.apps.core.tasks import (
    enqueue_transcode,
    transcode_video_job,
)

__all__ = ["enqueue_transcode", "transcode_video_job"]
