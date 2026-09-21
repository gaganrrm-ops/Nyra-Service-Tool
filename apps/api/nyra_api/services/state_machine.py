"""Record state machines. Guards and required fields per transition (incident first; others land day 15+)."""

from __future__ import annotations

from typing import Any

INCIDENT_STATES = ["new", "in_progress", "on_hold", "resolved", "closed", "cancelled"]

INCIDENT_TRANSITIONS: dict[str, list[str]] = {
    "new": ["in_progress", "on_hold", "cancelled"],
    "in_progress": ["on_hold", "resolved", "cancelled"],
    "on_hold": ["in_progress", "resolved", "cancelled"],
    "resolved": ["closed", "in_progress"],   # in_progress = reopen
    "closed": ["in_progress"],               # reopen inside the reopen window
    "cancelled": [],
}

REQUIRED_FIELDS: dict[tuple[str, str], list[str]] = {
    ("in_progress", "resolved"): ["resolution_notes"],
    ("on_hold", "resolved"): ["resolution_notes"],
    ("new", "cancelled"): ["state_reason"],
}

ON_HOLD_REASONS = ["awaiting_caller", "awaiting_vendor", "awaiting_change", "awaiting_parts", "scheduled_maintenance", "other"]


class TransitionError(ValueError):
    def __init__(self, message: str, missing: list[str] | None = None):
        super().__init__(message)
        self.missing = missing or []


def allowed(state: str) -> list[str]:
    return INCIDENT_TRANSITIONS.get(state, [])


def validate(record: dict[str, Any], target: str, payload: dict[str, Any]) -> None:
    current = record["state"]
    if target not in INCIDENT_TRANSITIONS.get(current, []):
        raise TransitionError(f"illegal transition {current} -> {target} (allowed: {', '.join(allowed(current)) or 'none'})")
    merged = {**record, **{k: v for k, v in payload.items() if v is not None}}
    missing = [f for f in REQUIRED_FIELDS.get((current, target), []) if not merged.get(f)]
    if missing:
        raise TransitionError(f"missing required field(s) for {current} -> {target}", missing)
    if target == "on_hold" and not merged.get("on_hold_reason"):
        raise TransitionError("on-hold reason is required", ["on_hold_reason"])
