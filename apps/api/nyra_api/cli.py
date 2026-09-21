"""Nyra CLI: migrations, seeds, diagnostics and smoke tests.

Usage:
  python -m nyra_api.cli db:migrate [--url URL]
  python -m nyra_api.cli db:seed
  python -m nyra_api.cli db:status
  python -m nyra_api.cli doctor
  python -m nyra_api.cli smoke
  python -m nyra_api.cli serve
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import typer

from . import db, repo
from .config import settings

app = typer.Typer(add_completion=False, help="Nyra Service Tool CLI")


def _banner(title: str) -> None:
    typer.echo("")
    typer.echo(f"=== {title} " + "=" * max(0, 60 - len(title)))


def _purge_test_rows() -> int:
    """Remove rows created by the automated test suite (tagged 'pytest')."""
    if not db.query("select to_regclass('public.record') as t")[0]["t"]:
        return 0
    removed = db.execute("delete from record where 'pytest' = any(tags)")
    db.execute("delete from notification_send_log where record_id is null or recipients::text = '[]'")
    return removed


@app.command("db:reset")
def db_reset(
    yes: bool = typer.Option(False, "--yes", help="required: confirms destructive reset of business data"),
) -> None:
    """Truncate all business tables and re-apply migrations + demo seed (demo refresh)."""
    _banner("db:reset")
    if not yes:
        typer.echo("refusing to run without --yes (this destroys all records, people and configuration)")
        raise typer.Exit(code=1)
    tables = db.query(
        """
        select tablename from pg_tables
        where schemaname='public' and tablename not in ('schema_migrations','seed_history')
        order by tablename
        """
    )
    names = ", ".join(t["tablename"] for t in tables)
    typer.echo(f"truncating {len(tables)} tables")
    db.execute("truncate " + names + " restart identity cascade")
    db.execute("delete from seed_history")
    _apply_dir(settings().migrations_dir, "schema_migrations", "migration", force=True)
    _apply_dir(settings().seeds_dir, "seed_history", "seed", force=True)
    typer.echo("reset complete - demo data reloaded")


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _apply_dir(dir_path: Path, registry: str, label: str, force: bool = False) -> int:
    db.ensure_registry_tables()
    files = sorted(dir_path.glob("*.sql"))
    if not files:
        typer.echo(f"no {label} files in {dir_path}")
        return 0
    applied = 0
    for f in files:
        body = f.read_text(encoding="utf-8")
        if not force:
            row = db.query_one("select filename from " + registry + " where filename=%s", (f.name,))
            if row:
                typer.echo(f"  skip   {f.name} (already applied)")
                continue
        typer.echo(f"  apply  {f.name} ({len(body)} chars)")
        db.execute(body)
        db.execute("insert into " + registry + " (filename, checksum) values (%s,%s) on conflict (filename) do nothing",
                   (f.name, _checksum(body)))
        applied += 1
    return applied


@app.command("db:migrate")
def db_migrate(
    url: str | None = typer.Option(None, "--url", help="database URL override (e.g. Supabase)"),
    force: bool = typer.Option(False, "--force", help="re-apply files even if recorded"),
) -> None:
    """Apply db/migrations in filename order."""
    if url:
        db.pool.cache_clear() if hasattr(db.pool, "cache_clear") else None
        import os

        os.environ["DATABASE_URL"] = url
        settings.cache_clear()
    cfg = settings()
    _banner("db:migrate")
    typer.echo(f"target: {cfg.database_url.split('@')[-1]}")
    n = _apply_dir(cfg.migrations_dir, "schema_migrations", "migration", force)
    typer.echo(f"migrations applied: {n}")


@app.command("db:seed")
def db_seed(force: bool = typer.Option(False, "--force", help="re-apply seeds even if recorded")) -> None:
    """Load demo data (2 organisations)."""
    cfg = settings()
    _banner("db:seed")
    n = _apply_dir(cfg.seeds_dir, "seed_history", "seed", force)
    typer.echo(f"seed files applied: {n}")
    db: dict = repo.counts(1)
    for k, v in db.items():
        typer.echo(f"  {k:24s} {v}")


@app.command("db:status")
def db_status() -> None:
    """Row counts and applied migration/seed state."""
    _banner("db:status")
    info = db.ping()
    typer.echo(f"database : {info.get('db')}")
    typer.echo(f"server   : {(info.get('version') or '')[:60]}")
    state = repo.seed_state()
    typer.echo(f"migrations applied: {len(state['migrations'])}")
    typer.echo(f"seeds applied     : {len(state['seeds'])}")
    tenants = db.query("select id, slug, name from tenant order by id")
    if not tenants:
        typer.echo("no tenants - run db:migrate then db:seed")
        return
    for t in tenants:
        typer.echo("")
        typer.echo(f"tenant {t['id']}: {t['name']} ({t['slug']})")
        for k, v in repo.counts(t["id"]).items():
            typer.echo(f"  {k:24s} {v}")


@app.command("doctor")
def doctor() -> None:
    """Environment + database diagnostics."""
    _banner("doctor")
    cfg = settings()
    typer.echo(f"python           : {sys.version.split()[0]}")
    typer.echo(f"app_env          : {cfg.app_env}")
    typer.echo(f"auth_mode        : {cfg.auth_mode}")
    typer.echo(f"repository root  : {Path(__file__).resolve().parents[3]}")
    typer.echo(f"migrations dir   : {cfg.migrations_dir} ({len(list(cfg.migrations_dir.glob('*.sql')))} files)")
    typer.echo(f"seeds dir        : {cfg.seeds_dir} ({len(list(cfg.seeds_dir.glob('*.sql')))} files)")
    typer.echo(f"ai_enabled       : {cfg.ai_enabled} (provider: {cfg.llm_provider or 'unset'})")
    typer.echo(f"smtp configured  : {bool(cfg.smtp_host)}")
    typer.echo(f"imap configured  : {bool(cfg.imap_host)}")
    target = cfg.database_url.split("@")[-1] if "@" in cfg.database_url else cfg.database_url
    typer.echo(f"database target  : {target}")
    try:
        info = db.ping()
        typer.echo(f"database         : OK ({info.get('db')})")
    except Exception as exc:
        typer.echo(f"database         : FAILED - {exc}")
        raise typer.Exit(code=1)
    state = repo.seed_state()
    typer.echo(f"migrations/seeds : {len(state['migrations'])}/{len(state['seeds'])}")
    typer.echo("doctor: OK")


@app.command("smoke")
def smoke() -> None:
    """End-to-end checks against a seeded database (no server required)."""
    _banner("smoke")
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        typer.echo(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    tenant = repo.default_tenant()
    check("tenant exists", bool(tenant), str((tenant or {}).get("slug")))

    counts = repo.counts(1)
    check("people seeded", (counts.get("people") or 0) >= 10, f"{counts.get('people')} people")
    check("teams seeded with DLs", (counts.get("teams") or 0) >= 8, f"{counts.get('teams')} teams")
    check("incidents seeded", (counts.get("incidents") or 0) >= 8, f"{counts.get('incidents')} incidents")
    check("knowledge seeded", (counts.get("kb_articles") or 0) >= 4, f"{counts.get('kb_articles')} articles")
    check("notification templates seeded", (counts.get("notification_templates") or 0) >= 10,
          f"{counts.get('notification_templates')} templates")

    ctx = repo.person_context(20)
    check("caller context has (i) sections",
          all(k in ctx for k in ("identity", "contact", "employment", "access", "service_context")),
          f"keys={','.join(ctx.keys())}")
    check("VIP flagged on caller", bool(ctx.get("service_context", {}).get("is_vip")))
    agent_ctx = repo.person_context(2)
    check("team DL address exposed for an agent", bool(agent_ctx.get("employment", {}).get("team_email")),
          str(agent_ctx.get("employment", {}).get("team_email")))
    check("caller with no team handled", "team_email" in ctx.get("employment", {}))

    queue = repo.list_records(1, type_="incident", open_only=True, limit=50)
    check("open incident queue query works", len(queue) >= 5, f"{len(queue)} open")
    check("priority ordering respected", [r["priority"] for r in queue] == sorted(r["priority"] for r in queue))
    check("SLA remaining computed", any(r.get("sla_remaining_minutes") is not None for r in queue))

    kb = repo.search_kb(1, "vpn")
    check("kb full-text search works", len(kb) >= 1, f"{len(kb)} hits for 'vpn'")

    detail = repo.record_detail(1)
    check("record detail assembles", bool(detail) and "comments" in (detail or {}))
    check("work notes + public comments present", len((detail or {}).get("comments") or []) >= 2)

    audit_rows = repo.list_audit(1, entity_type="record", limit=10)
    typer.echo(f"  [INFO] audit rows for records: {len(audit_rows)}")

    typer.echo("")
    if failures:
        typer.echo(f"smoke FAILED: {', '.join(failures)}")
        raise typer.Exit(code=1)
    typer.echo("smoke: ALL CHECKS PASSED")


@app.command("serve")
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Run the API with uvicorn."""
    import uvicorn

    uvicorn.run("nyra_api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
