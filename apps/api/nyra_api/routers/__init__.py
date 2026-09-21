"""HTTP routers: validation, auth dependency and response shaping only. Business rules live in services/."""

from . import audit, health, incidents, kb, meta, people, teams  # noqa: F401
