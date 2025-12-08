"""Type definitions for Discord URL reference parsing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReferenceType(Enum):
    """Type of reference parsed from a URL in a Discord message."""

    LOG_ENTRY = "log_entry"
    PROBLEM_REPORT = "problem_report"
    PART_REQUEST = "part_request"
    PART_REQUEST_UPDATE = "part_request_update"
    MACHINE = "machine"


@dataclass
class ParsedReference:
    """A reference parsed from a Flipfix URL."""

    ref_type: ReferenceType
    object_id: int | None = None
    machine_slug: str | None = None
