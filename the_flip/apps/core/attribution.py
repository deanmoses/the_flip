"""User attribution helpers for forms with maintainer autocomplete fields.

These helpers resolve user attribution from the maintainer autocomplete component,
which submits both a hidden username field (from autocomplete selection) and a
visible text field (for freeform input).

Two patterns:
- CREATE views: Handle shared account logic (shared accounts require explicit name)
- EDIT views: Simple username lookup with freetext fallback
"""

from dataclasses import dataclass

from django.http import HttpRequest

from the_flip.apps.accounts.models import Maintainer


@dataclass
class AttributionResult:
    """Result of resolving user attribution from form input."""

    maintainer: Maintainer | None
    freetext_name: str


def resolve_maintainer_for_create(
    request: HttpRequest,
    current_maintainer: Maintainer,
    form,
    username_field: str = "requester_name_username",
    text_field: str = "requester_name",
    error_message: str = "Please enter your name.",
) -> AttributionResult | None:
    """
    Resolve maintainer attribution for CREATE views.

    Handles shared account logic:
    - Shared accounts: username lookup → freetext fallback → error (required)
    - Non-shared accounts: default to current user, username selection overrides

    Args:
        request: The HTTP request containing POST data
        current_maintainer: The logged-in user's maintainer profile
        form: The form to add errors to if validation fails
        username_field: POST field name for hidden username (default: requester_name_username)
        text_field: Form field name for visible text input (default: requester_name)
        error_message: Error message if attribution is required but missing

    Returns:
        AttributionResult with maintainer and/or freetext_name, or None if validation fails
    """
    username = request.POST.get(username_field, "").strip()
    text = form.cleaned_data.get(text_field, "").strip()

    if current_maintainer.is_shared_account:
        # Shared accounts: require explicit attribution
        maintainer = _lookup_maintainer(username) if username else None
        if maintainer:
            return AttributionResult(maintainer, "")
        if text:
            return AttributionResult(None, text)
        form.add_error(text_field, error_message)
        return None
    else:
        # Non-shared accounts: username lookup → freetext fallback → current user
        if username:
            matched = _lookup_maintainer(username)
            if matched:
                return AttributionResult(matched, "")
        if text:
            return AttributionResult(None, text)
        return AttributionResult(current_maintainer, "")


def resolve_maintainer_for_edit(
    request: HttpRequest,
    form,
    username_field: str,
    text_field: str,
    error_message: str = "Please enter a name.",
) -> AttributionResult | None:
    """
    Resolve maintainer attribution for EDIT views.

    Simple logic: username lookup → freetext fallback → error.
    No shared account handling (editing existing record, not creating new one).

    Args:
        request: The HTTP request containing POST data
        form: The form to add errors to if validation fails
        username_field: POST field name for hidden username
        text_field: Form field name for visible text input
        error_message: Error message if attribution is required but missing

    Returns:
        AttributionResult with maintainer and/or freetext_name, or None if validation fails
    """
    username = request.POST.get(username_field, "").strip()
    text = form.cleaned_data.get(text_field, "").strip()

    maintainer = _lookup_maintainer(username) if username else None
    if maintainer:
        return AttributionResult(maintainer, "")
    if text:
        return AttributionResult(None, text)

    form.add_error(text_field, error_message)
    return None


def _lookup_maintainer(username: str) -> Maintainer | None:
    """Look up non-shared maintainer by username (case-insensitive)."""
    return Maintainer.objects.filter(
        user__username__iexact=username,
        is_shared_account=False,
    ).first()
