"""Reference data: tenant, counts, taxonomy, teams, services, SLA policies, priorities, saved views."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import repo
from ..security import Principal, current_principal
from ..services import priority as prio
from ..services import numbering

router = APIRouter(prefix="/api/v1/meta", tags=["reference data"])


@router.get("/summary")
def summary(principal: Principal = Depends(current_principal)) -> dict:
    tenant = repo.default_tenant() or {}
    return {
        "tenant": {"id": tenant.get("id"), "slug": tenant.get("slug"), "name": tenant.get("name")},
        "counts": repo.counts(principal.tenant_id),
        "priorities": prio.PRIORITY_LABELS,
        "next_number_preview": {
            key: numbering.peek(principal.tenant_id, key)
            for key in ("incident", "problem", "change", "request", "kb")
        },
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/priorities")
def priorities() -> dict:
    return {"labels": prio.PRIORITY_LABELS, "impact": prio.IMPACT_LABELS, "urgency": prio.URGENCY_LABELS, "matrix": prio.matrix_as_table()}


@router.get("/taxonomy")
def taxonomy(domain: str | None = None, principal: Principal = Depends(current_principal)) -> list[dict]:
    return repo.list_taxonomy(principal.tenant_id, domain)


@router.get("/teams")
def teams(domain: str | None = None, principal: Principal = Depends(current_principal)) -> list[dict]:
    return repo.list_teams(principal.tenant_id, domain)


@router.get("/teams/{team_id}/members")
def team_members(team_id: int, principal: Principal = Depends(current_principal)) -> list[dict]:
    return repo.team_members(team_id)


@router.get("/org-units")
def org_units(kind: str | None = None, principal: Principal = Depends(current_principal)) -> list[dict]:
    return repo.list_org_units(principal.tenant_id, kind)


@router.get("/services")
def services(principal: Principal = Depends(current_principal)) -> list[dict]:
    return repo.list_services(principal.tenant_id)


@router.get("/sla-policies")
def sla_policies(principal: Principal = Depends(current_principal)) -> list[dict]:
    return repo.list_sla_policies(principal.tenant_id)


@router.get("/views")
def saved_views(shared_only: bool = Query(default=False), principal: Principal = Depends(current_principal)) -> list[dict]:
    views = repo.list_saved_views(principal.tenant_id, principal.person_id)
    return [v for v in views if v["shared"]] if shared_only else views


@router.get("/views/{view_id}/records")
def run_view(view_id: int, limit: int = 50, principal: Principal = Depends(current_principal)) -> dict:
    views = [v for v in repo.list_saved_views(principal.tenant_id, principal.person_id) if v["id"] == view_id]
    if not views:
        raise HTTPException(404, "view not found")
    view = views[0]
    f = view.get("filters") or {}
    # A missing key means "no filter"; an explicit null value means "unassigned".
    explicit_unassigned = ("assignee" in f and f["assignee"] is None) or ("assignee_id" in f and f["assignee_id"] is None)
    assignee_filter = f.get("assignee_id")
    if f.get("assignee") == "me":
        assignee_filter = principal.person_id
    rows = repo.list_records(
        principal.tenant_id,
        type_=None,
        state=f.get("state"),
        assignee_id=None if explicit_unassigned else assignee_filter,
        unassigned=True if explicit_unassigned else None,
        assignment_group_id=f.get("assignment_group_id"),
        priority=f.get("priority"),
        sla_state=f.get("sla_state"),
        major_incident=f.get("major_incident"),
        open_only=f.get("open"),
        search=f.get("q"),
        sort=view.get("sort") or "priority",
        limit=limit,
    )
    return {"view": {"id": view["id"], "name": view["name"], "columns": view.get("columns")}, "count": len(rows), "records": rows}
