"""Database access: one pooled connection factory plus a tiny SQL helper layer.

All SQL lives in this module or in `repo.py`. Statements are parameterised; user input is never interpolated.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, Sequence

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

log = logging.getLogger("nyra.db")
_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings().database_url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row, "autocommit": False},
            open=True,
            timeout=15,
        )
    return _pool


@contextmanager
def cursor(commit: bool = False) -> Iterator[psycopg.Cursor]:
    with pool().connection() as conn:
        with conn.cursor() as cur:
            yield cur
            if commit:
                conn.commit()


def query(sql: str, params: Sequence[Any] | dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall() if cur.description else []


def query_one(sql: str, params: Sequence[Any] | dict[str, Any] | None = None) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: Sequence[Any] | dict[str, Any] | None = None) -> int:
    with cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.rowcount


def execute_returning(sql: str, params: Sequence[Any] | dict[str, Any] | None = None) -> dict[str, Any] | None:
    with cursor(commit=True) as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def executemany(sql: str, seq: Iterable[Sequence[Any]]) -> int:
    with cursor(commit=True) as cur:
        cur.executemany(sql, seq)
        return cur.rowcount


def ping() -> dict[str, Any]:
    row = query_one("select version() as version, current_database() as db, now() as ts")
    return row or {}


def ensure_registry_tables() -> None:
    """Migration/seed bookkeeping tables (created by the CLI, not by a migration)."""
    execute(
        """
        create table if not exists schema_migrations (
          filename text primary key, applied_at timestamptz not null default now(), checksum text
        );
        create table if not exists seed_history (
          filename text primary key, applied_at timestamptz not null default now(), checksum text
        );
        alter table seed_history add column if not exists checksum text;
        alter table schema_migrations add column if not exists checksum text;
        """
    )
