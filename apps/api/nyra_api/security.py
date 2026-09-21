"""Authentication and authorisation.

Prototype note (`# prototype depth`): with AUTH_MODE=dev the caller identity is taken from headers so the API can be
exercised without an IdP. With AUTH_MODE=supabase the bearer JWT issued by Supabase Auth is verified and the subject is
mapped to a `person` row. Role checks are enforced here; row visibility rules live in `services/access.py` (day 3).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings
from . import repo

ROLE_ORDER = ["end_user", "agent_l1", "agent_l2", "agent_l3", "team_lead", "service_owner", "admin"]


@dataclass
class Principal:
    person_id: int
    tenant_id: int
    display_name: str
    roles: list[str] = field(default_factory=list)

    @property
    def is_agent(self) -> bool:
        return any(r.startswith("agent") or r in ("team_lead", "service_owner", "admin") for r in self.roles)

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    def require(self, *roles: str) -> None:
        if not set(roles) & set(self.roles) and not self.is_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires one of roles: {', '.join(roles)}")


def _load_person(person_id: int) -> Principal:
    row = repo.get_person(person_id)
    if not row:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown principal")
    return Principal(
        person_id=row["id"],
        tenant_id=row["tenant_id"],
        display_name=row["display_name"],
        roles=list(row.get("roles") or []),
    )


def current_principal(
    authorization: str | None = Header(default=None),
    x_nyra_person_id: int | None = Header(default=None, alias="X-Nyra-Person-Id"),
) -> Principal:
    cfg = settings()
    if cfg.auth_mode == "supabase" and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            claims = jwt.decode(token, cfg.supabase_jwt_secret or None, options={"verify_signature": bool(cfg.supabase_jwt_secret), "verify_aud": False})
        except jwt.PyJWTError as exc:  # pragma: no cover - depends on external IdP
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}") from exc
        email = claims.get("email")
        row = repo.get_person_by_email(email) if email else None
        if not row:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "no Nyra person mapped to this identity")
        return _load_person(row["id"])

    if x_nyra_person_id:
        return _load_person(x_nyra_person_id)

    if cfg.app_env == "dev":
        return _load_person(repo.default_principal_id())

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")


def agent(principal: Principal = Depends(current_principal)) -> Principal:
    if not principal.is_agent:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "agent role required")
    return principal
