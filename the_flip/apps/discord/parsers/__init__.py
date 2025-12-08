"""Discord message reference parsing.

This package provides URL parsing for Flipfix references in Discord messages.

Public API:
- parse_url: Parse a Flipfix URL to extract object references
- ReferenceType: Enum of reference types found in URLs
- ParsedReference: A reference found in a URL
"""

from .references import parse_url
from .types import ParsedReference, ReferenceType

__all__ = [
    "parse_url",
    "ReferenceType",
    "ParsedReference",
]
