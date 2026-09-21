"""People: list, detail and the caller-context bundle used by the (i) popover."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import repo
from ..security import Principal, agent, current_principal

router = APIRouter(prefix="/api/v1/people", tags=["people"])


@router.get("")
def list_people(
    search: str | None = None,
    active: bool | None = None,
    vip: bool | None = None,
    department_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(current_principal),
) -> dict:
    rows = repo.list_people(
        principal.tenant_id,
        search=search,
        active=active,
        vip=vip,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )
    return {"count": len(rows), "limit": limit, "offset": offset, "people": rows}


@router.get("/me")
def me(principal: Principal = Depends(current_principal)) -> dict:
    return {
        "principal": {
            "person_id": principal.person_id,
            "tenant_id": principal.tenant_id,
            "display_name": principal.display_name,
            "roles": principal.roles,
            "is_agent": principal.is_agent,
            "is_admin": principal.is_admin,
        }
    }


@router.get("/{person_id}")
def get_person(person_id: int, principal: Principal = Depends(current_principal)) -> dict:
    row = repo.get_person(person_id)
    if not row or row["tenant_id"] != principal.tenant_id:
        raise HTTPException(404, "person not found")
    return row


@router.get("/{person_id}/context")
def person_context(person_id: int, principal: Principal = Depends(agent)) -> dict:
    ctx = repo.person_context(person_id)
    if not ctx:
        raise HTTPException(404, "person not found")
    return ctx
