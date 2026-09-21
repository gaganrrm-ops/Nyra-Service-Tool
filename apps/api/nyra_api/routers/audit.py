"""Audit trail and notification proof-of-send read APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from .. import db, repo
from ..security import Principal, agent

router = APIRouter(prefix="/api/v1", tags=["audit & notifications"])


@router.get("/audit")
def audit(
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    principal: Principal = Depends(agent),
) -> dict:
    rows = repo.list_audit(principal.tenant_id, entity_type=entity_type, entity_id=entity_id, limit=limit)
    return {"count": len(rows), "entries": rows}


@router.get("/notifications/templates")
def templates(principal: Principal = Depends(agent)) -> dict:
    rows = db.query(
        """
        select id, code, event, channel, locale, subject, version, active
        from notification_template where tenant_id=%s order by event, code
        """,
        (principal.tenant_id,),
    )
    return {"count": len(rows), "templates": rows}


@router.get("/notifications/audiences")
def audiences(principal: Principal = Depends(agent)) -> dict:
    rows = db.query(
        "select id, code, name, audience_type, expansion_mode, privacy_class, expression from notification_audience where tenant_id=%s order by code",
        (principal.tenant_id,),
    )
    return {"count": len(rows), "audiences": rows}


@router.get("/notifications/log")
def send_log(
    record_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    principal: Principal = Depends(agent),
) -> dict:
    if record_id:
        rows = db.query(
            """
            select * from notification_send_log where tenant_id=%s and record_id=%s
            order by created_at desc limit %s
            """,
            (principal.tenant_id, record_id, limit),
        )
    else:
        rows = db.query(
            "select * from notification_send_log where tenant_id=%s order by created_at desc limit %s",
            (principal.tenant_id, limit),
        )
    return {"count": len(rows), "entries": rows}
