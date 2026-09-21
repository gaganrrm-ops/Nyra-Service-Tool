"""Shared fixtures. Database-backed tests skip (not fail) when no database is reachable, so `make api-test`
works on a laptop with nothing running.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://nyra@127.0.0.1:5434/nyra"))
os.environ.setdefault("APP_ENV", "dev")

from nyra_api import db  # noqa: E402


def _db_available() -> bool:
    try:
        db.ping()
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_available()
requires_db = pytest.mark.skipif(not DB_AVAILABLE, reason="no database reachable (set DATABASE_URL)")


@pytest.fixture(scope="session")
def seeded() -> bool:
    if not DB_AVAILABLE:
        return False
    row = db.query_one("select count(*) as n from record")
    return bool(row and row["n"] > 0)


@pytest.fixture(scope="session", autouse=True)
def purge_test_records():
    """Integration tests create real rows; remove every record they tagged so the demo data stays clean."""
    yield
    if not DB_AVAILABLE:
        return
    try:
        db.execute("delete from notification_send_log where record_id in (select id from record where 'pytest' = any(tags))")
        db.execute("delete from record_comment where record_id in (select id from record where 'pytest' = any(tags))")
        db.execute("delete from record_relationship where record_id in (select id from record where 'pytest' = any(tags))")
        db.execute("delete from audit_log where entity_type='record' and entity_id in (select id from record where 'pytest' = any(tags))")
        db.execute("delete from record where 'pytest' = any(tags)")
    except Exception:  # pragma: no cover - cleanup must never mask a real failure
        pass
