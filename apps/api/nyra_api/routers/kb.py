"""Knowledge: search, read, feedback (thin slice for the portal + AI KB suggestions)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import db, repo
from ..security import Principal, current_principal

router = APIRouter(prefix="/api/v1/kb", tags=["knowledge"])


@router.get("")
def search(
    q: str | None = None,
    scope: str = Query(default="portal", pattern="^(internal|portal|public|all)$"),
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(current_principal),
) -> dict:
    visibility = None if scope == "all" else (["internal", "portal", "public"] if scope == "internal" else [scope, "public"])
    rows = repo.search_kb(principal.tenant_id, q, visibility=visibility, limit=limit)
    return {"count": len(rows), "query": q, "scope": scope, "articles": rows}


@router.get("/{article_id}")
def get_article(article_id: int, principal: Principal = Depends(current_principal)) -> dict:
    row = repo.get_kb(article_id)
    if not row or row["tenant_id"] != principal.tenant_id or row["state"] != "published":
        raise HTTPException(404, "article not found")
    db.execute("update kb_article set hit_count = hit_count + 1 where id=%s", (article_id,))
    return row


@router.post("/{article_id}/feedback", status_code=201)
def feedback(article_id: int, helpful: bool, comment: str | None = None, principal: Principal = Depends(current_principal)) -> dict:
    article = repo.get_kb(article_id)
    if not article or article["tenant_id"] != principal.tenant_id:
        raise HTTPException(404, "article not found")
    column = "helpful_count" if helpful else "not_helpful_count"
    db.execute("update kb_article set " + column + " = " + column + " + 1 where id=%s", (article_id,))
    db.execute(
        "insert into kb_feedback (article_id, person_id, helpful, comment) values (%s,%s,%s,%s)",
        (article_id, principal.person_id, helpful, comment),
    )
    return {"ok": True, "article_id": article_id, "helpful": helpful}
