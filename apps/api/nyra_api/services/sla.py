"""SLA clocks: business-calendar aware target calculation plus at-risk/breach evaluation."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from .. import db

WEEKDAY_ISO = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7}


def _holidays(calendar_id: int | None, inline: list | None = None) -> set[date]:
    """Holidays may be supplied inline (tests, previews) or read from the business calendar row."""
    raw = inline
    if raw is None:
        if not calendar_id:
            return set()
        row = db.query_one("select holidays from business_calendar where id=%s", (calendar_id,))
        raw = (row or {}).get("holidays") or []
    out: set[date] = set()
    for h in raw:
        try:
            out.add(date.fromisoformat(h))
        except (TypeError, ValueError):
            continue
    return out


def is_working_day(d: date, work_days: list[int], holidays: set[date]) -> bool:
    return WEEKDAY_ISO[d.weekday()] in work_days and d not in holidays


def add_business_minutes(start: datetime, minutes: int, calendar: dict | None) -> datetime:
    """Add `minutes` of working time. Calendar default: Mon-Fri 09:00-18:00 Asia/Kolkata."""
    if minutes is None:
        return start
    if not calendar:
        return start + timedelta(minutes=minutes)

    work_days = list(calendar.get("work_days") or [1, 2, 3, 4, 5])
    work_start: time = calendar.get("work_start") or time(9, 0)
    work_end: time = calendar.get("work_end") or time(18, 0)
    holidays = _holidays(calendar.get("id"), calendar.get("holidays"))

    remaining = float(minutes)
    cursor_dt = start
    guard = 0
    while remaining > 0 and guard < 4000:
        guard += 1
        d = cursor_dt.date()
        if not is_working_day(d, work_days, holidays):
            cursor_dt = datetime.combine(d + timedelta(days=1), work_start, tzinfo=start.tzinfo)
            continue
        day_start = datetime.combine(d, work_start, tzinfo=start.tzinfo)
        day_end = datetime.combine(d, work_end, tzinfo=start.tzinfo)
        if cursor_dt < day_start:
            cursor_dt = day_start
        if cursor_dt >= day_end:
            cursor_dt = datetime.combine(d + timedelta(days=1), work_start, tzinfo=start.tzinfo)
            continue
        available = (day_end - cursor_dt).total_seconds() / 60.0
        if available >= remaining:
            return cursor_dt + timedelta(minutes=remaining)
        remaining -= available
        cursor_dt = datetime.combine(d + timedelta(days=1), work_start, tzinfo=start.tzinfo)
    return cursor_dt


def calendar_for(calendar_id: int | None) -> dict | None:
    if not calendar_id:
        return None
    return db.query_one(
        "select id, name, timezone, work_days, work_start, work_end, holidays from business_calendar where id=%s",
        (calendar_id,),
    )


def select_policy(tenant_id: int, applies_to: str, priority: int, service_id: int | None, team_id: int | None) -> dict | None:
    """Most specific matching policy wins: team+service > service > team > priority-only."""
    rows = db.query(
        """
        select * from sla_policy
        where tenant_id=%s and active and (applies_to=%s or applies_to='any')
          and (match_priority is null or %s = any(match_priority))
          and (match_service_id is null or match_service_id = %s)
          and (match_team_id is null or match_team_id = %s)
        order by (match_team_id is not null) desc, (match_service_id is not null) desc, resolution_minutes nulls last
        """,
        (tenant_id, applies_to, priority, service_id, team_id),
    )
    return rows[0] if rows else None


def targets(policy: dict | None, opened_at: datetime, calendar: dict | None) -> dict:
    if not policy:
        return {"response_due_at": None, "resolve_due_at": None, "sla_policy_id": None}
    if policy.get("use_business_hours"):
        cal = calendar or calendar_for(policy.get("calendar_id"))
    else:
        cal = None
    return {
        "sla_policy_id": policy["id"],
        "response_due_at": add_business_minutes(opened_at, policy["response_minutes"], cal) if policy.get("response_minutes") else None,
        "resolve_due_at": add_business_minutes(opened_at, policy["resolution_minutes"], cal) if policy.get("resolution_minutes") else None,
    }


def evaluate(record: dict, now: datetime | None = None) -> dict:
    """Return sla_state + elapsed percentage for the resolution target (prototype: single clock per record)."""
    now = now or datetime.now(timezone.utc)
    due = record.get("resolve_due_at")
    if not due:
        return {"sla_state": "ok", "sla_percent": None, "sla_remaining_minutes": None, "sla_target_type": "resolution"}
    opened = record.get("opened_at") or now
    total = (due - opened).total_seconds() / 60.0 or 1.0
    used = (now - opened).total_seconds() / 60.0
    pct = max(0.0, min(100.0, used / total * 100.0))
    state = "breached" if now > due else ("at_risk" if pct >= 75 else "ok")
    return {
        "sla_state": state,
        "sla_percent": round(pct, 1),
        "sla_remaining_minutes": int((due - now).total_seconds() / 60.0),
        "sla_target_type": "resolution",
    }
