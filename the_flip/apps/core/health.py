"""Health check helpers."""

from __future__ import annotations

from django.db import connection

from the_flip.apps.catalog.models import MachineInstance


def check_db_and_orm() -> dict:
    """Verify DB connectivity and ORM access by touching machines table."""
    details: dict[str, object] = {}
    # Ensure low-level connection is healthy
    connection.ensure_connection()
    details["db"] = "ok"

    # Minimal ORM touch: confirm machines table is reachable
    machine_exists = MachineInstance.objects.order_by("id").values_list("id", flat=True).first()
    details["orm_machine_sample"] = machine_exists if machine_exists is not None else "none"
    return details
