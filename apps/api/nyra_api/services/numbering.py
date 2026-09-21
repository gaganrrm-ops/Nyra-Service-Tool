"""Record numbering: transactional per-tenant sequences (INC0000001, PRB, CHG, REQ, RITM, TASK, KB)."""

from __future__ import annotations

from psycopg.types.json import Jsonb

from .. import db

PREFIX_DEFAULTS = {"incident": "INC", "problem": "PRB", "change": "CHG", "request": "REQ", "ritm": "RITM", "task": "TASK", "problem_task": "PTASK", "change_task": "CTASK", "catalog_task": "TASK", "kb": "KB"}


def next_number(tenant_id: int, key: str) -> str:
    """Atomically allocate the next number. Uses UPDATE ... RETURNING so concurrent inserts cannot collide."""
    prefix = PREFIX_DEFAULTS.get(key, key[:3].upper())
    row = db.execute_returning(
        """
        insert into numbering_sequence (tenant_id, key, prefix, next_value, padding)
        values (%(tenant_id)s, %(key)s, %(prefix)s, 2, 7)
        on conflict (tenant_id, key) do update set next_value = numbering_sequence.next_value + 1
        returning prefix, padding, next_value
        """,
        {"tenant_id": tenant_id, "key": key, "prefix": prefix},
    )
    assert row is not None
    return f"{row['prefix']}{str(row['next_value'] - 1).zfill(row['padding'])}"


def peek(tenant_id: int, key: str) -> str:
    row = db.query_one(
        "select prefix, padding, next_value from numbering_sequence where tenant_id=%s and key=%s",
        (tenant_id, key),
    )
    if not row:
        return "-"
    return f"{row['prefix']}{str(row['next_value']).zfill(row['padding'])}"
