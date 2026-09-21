"""Health, version and readiness."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from .. import db
from ..config import settings
from .. import __version__

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    try:
        info = db.ping()
        db_ok, detail = True, {"database": info.get("db"), "server": (info.get("version") or "")[:40]}
    except Exception as exc:  # pragma: no cover - depends on environment
        db_ok, detail = False, {"error": str(exc)}
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "nyra-api",
        "version": __version__,
        "env": settings().app_env,
        "database_connected": db_ok,
        "ai_enabled": settings().ai_enabled,
        "auth_mode": settings().auth_mode,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "detail": detail,
    }
