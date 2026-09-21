"""Audit trail: one row per changed field, plus explicit business events (major incident declared, SLA breached)."""

from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from .. import db

AUDITED_FIELDS = [
    "state", "priority", "urgency", "impact", "assignment_group_id", "assignee_id", "category_id", "subcategory_id",
    "service_id", "ci_id", "major_incident", "escalation", "resolution_code", "resolution_notes", "on_hold_reason",
    "short_description", "quality_miss", "security_flag", "regulatory_flag",
]


def diff(before: dict[str, Any], after: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    out = []
    for field in AUDITED_FIELDS:
        if field in after and before.get(field) != after.get(field):
            out.append((field, before.get(field), after.get(field)))
    return out


def write(
    tenant_id: int,
    entity_type: str,
    entity_id: int | None,
    action: str,
    *,
    field: str | None = None,
    old_value: Any = None,
    new_value: Any = None,
    actor_id: int | None = None,
    actor_type: str = "user",
    channel: str | None = None,
) -> None:
    db.execute(
        """
        insert into audit_log (tenant_id, entity_type, entity_id, action, field, old_value, new_value,
                               actor_id, actor_type, channel)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            tenant_id,
            entity_type,
            entity_id,
            action,
            field,
            None if old_value is None else str(old_value),
            None if new_value is None else str(new_value),
            actor_id,
            actor_type,
            channel,
        ),
    )


def write_diff(tenant_id: int, entity_type: str, entity_id: int, before: dict, after: dict, actor_id: int | None, channel: str | None = None) -> list[dict]:
    changes = []
    for field, old, new in diff(before, after):
        write(tenant_id, entity_type, entity_id, "updated", field=field, old_value=old, new_value=new, actor_id=actor_id, channel=channel)
        changes.append({"field": field, "old": old, "new": new})
    return changes
