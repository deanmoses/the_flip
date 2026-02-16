"""Validators for catalog models."""

from django import forms

from flipfix.apps.catalog.models import MachineInstance


def clean_machine_slug(cleaned_data: dict) -> str:
    """Validate that machine_slug refers to an existing machine."""
    slug = (cleaned_data.get("machine_slug") or "").strip()
    if not slug:
        return ""
    if MachineInstance.objects.filter(slug=slug).exists():
        return slug
    raise forms.ValidationError("Select a machine.")
