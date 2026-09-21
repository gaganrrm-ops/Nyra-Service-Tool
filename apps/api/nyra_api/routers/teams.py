"""Assignment groups (teams) including distribution-list addressing and queue load."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .. import repo
from ..security import Principal, current_principal

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get("")
def list_teams(domain: str | None = None, principal: Principal = Depends(current_principal)) -> dict:
    rows = repo.list_teams(principal.tenant_id, domain)
    return {"count": len(rows), "teams": rows}


@router.get("/{team_id}")
def get_team(team_id: int, principal: Principal = Depends(current_principal)) -> dict:
    teams = [t for t in repo.list_teams(principal.tenant_id) if t["id"] == team_id]
    if not teams:
        raise HTTPException(404, "team not found")
    team = teams[0]
    team["members"] = repo.team_members(team_id)
    return team
