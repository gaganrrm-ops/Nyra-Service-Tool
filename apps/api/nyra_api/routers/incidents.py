"""Incident queue, creation, transitions, comments. This is the day-1 golden path.

Creation pipeline (`# prototype depth`: notifications are logged, not yet sent - day 8):
  numbering -> priority matrix -> SLA target selection -> insert -> audit -> initial comment -> notification log stub
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import repo
from ..schemas import CommentCreate, IncidentCreate, IncidentPatch
from ..security import Principal, agent, current_principal
from ..services import audit as audit_svc
from ..services import numbering, priority as prio, sla as sla_svc
from ..services import state_machine as sm

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


def _load(record_id: int) -> dict:
    row = repo.get_record(record_id)
    if not row:
        raise HTTPException(404, "record not found")
    return row


@router.get("")
def list_incidents(
    state: list[str] | None = Query(default=None),
    open_only: bool = Query(default=False),
    assignee_id: int | None = None,
    mine: bool = Query(default=False),
    unassigned: bool | None = None,
    assignment_group_id: int | None = None,
    priority: list[int] | None = Query(default=None),
    sla_state: list[str] | None = Query(default=None),
    major_incident: bool | None = None,
    service_id: int | None = None,
    caller_id: int | None = None,
    q: str | None = None,
    sort: str = "priority",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(current_principal),
) -> dict:
    rows = repo.list_records(
        principal.tenant_id,
        type_="incident",
        state=state,
        assignee_id=principal.person_id if mine else assignee_id,
        unassigned=unassigned,
        assignment_group_id=assignment_group_id,
        priority=priority,
        sla_state=sla_state,
        major_incident=major_incident,
        open_only=open_only,
        service_id=service_id,
        caller_id=caller_id,
        search=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return {"count": len(rows), "limit": limit, "offset": offset, "sort": sort, "incidents": rows}


@router.get("/{record_id}")
def get_incident(record_id: int, principal: Principal = Depends(current_principal)) -> dict:
    row = repo.record_detail(record_id)
    if not row or row["tenant_id"] != principal.tenant_id:
        raise HTTPException(404, "incident not found")
    row["sla"] = sla_svc.evaluate(row)
    row["allowed_transitions"] = sm.allowed(row["state"])
    return row


@router.post("", status_code=201)
def create_incident(payload: IncidentCreate, principal: Principal = Depends(agent)) -> dict:
    tenant_id = principal.tenant_id
    caller = repo.get_person(payload.caller_id)
    if not caller or caller["tenant_id"] != tenant_id:
        raise HTTPException(422, "caller not found in this tenant")

    number = numbering.next_number(tenant_id, "incident")
    priority = payload.priority_override or prio.calculate(payload.impact, payload.urgency)
    opened_at = datetime.now(timezone.utc)

    group_id = payload.assignment_group_id
    if not group_id and payload.category_id:
        tax = [t for t in repo.list_taxonomy(tenant_id) if t["id"] == payload.category_id]
        group_id = (tax[0].get("default_team_id") if tax else None) or None
    group = None
    if group_id:
        matches = [t for t in repo.list_teams(tenant_id) if t["id"] == group_id]
        group = matches[0] if matches else None

    policy = sla_svc.select_policy(tenant_id, "incident", priority, payload.service_id, group_id)
    calendar = sla_svc.calendar_for((policy or {}).get("calendar_id") or (group or {}).get("calendar_id"))
    targets = sla_svc.targets(policy, opened_at, calendar)

    record = repo.create_record(
        {
            "tenant_id": tenant_id,
            "number": number,
            "type": "incident",
            "short_description": payload.short_description,
            "description": payload.description,
            "state": "new",
            "opened_by": caller["id"],
            "opened_at": opened_at,
            "caller_id": caller["id"],
            "channel": payload.channel,
            "contact_type": payload.channel,
            "assignment_group_id": group_id,
            "assignee_id": payload.assignee_id,
            "created_by": principal.person_id,
            "updated_by": principal.person_id,
            "priority": priority,
            "urgency": payload.urgency,
            "impact": payload.impact,
            "category_id": payload.category_id,
            "subcategory_id": payload.subcategory_id,
            "service_id": payload.service_id,
            "ci_id": payload.ci_id,
            "location_id": caller["location_id"],
            "department_id": caller["department_id"],
            "company_id": caller["company_id"],
            "major_incident": payload.major_incident,
            "parent_id": payload.parent_id,
            "root_id": payload.parent_id,
            "tags": payload.tags,
            "priority_override_reason": payload.priority_override_reason,
            "response_due_at": targets["response_due_at"],
            "resolve_due_at": targets["resolve_due_at"],
            "sla_policy_id": targets["sla_policy_id"],
        }
    )
    assert record is not None
    record_id = record["id"]

    audit_svc.write(
        tenant_id, "record", record_id, "created", new_value=f"{number} ({payload.channel})",
        actor_id=principal.person_id, channel=payload.channel,
    )
    if payload.priority_override and payload.priority_override != prio.calculate(payload.impact, payload.urgency):
        audit_svc.write(
            tenant_id, "record", record_id, "priority_override",
            field="priority", old_value=prio.calculate(payload.impact, payload.urgency),
            new_value=payload.priority_override, actor_id=principal.person_id, channel=payload.channel,
        )
    repo.add_comment(
        tenant_id, record_id, principal.person_id, "system",
        f"Incident {number} created via {payload.channel}. Priority {prio.label(priority)} "
        f"(impact {payload.impact} x urgency {payload.urgency})."
        + (f" Routed to {group['name']}." if group else " Awaiting assignment.")
        + (f" SLA policy: {policy['name']}." if policy else " No SLA policy matched."),
        source="system", is_internal=True,
    )
    if payload.work_notes:
        repo.add_comment(tenant_id, record_id, principal.person_id, "work_note", payload.work_notes, source="agent", is_internal=True)

    detail = repo.record_detail(record_id)
    assert detail is not None
    detail["sla"] = sla_svc.evaluate(detail)
    detail["notification_plan"] = [
        {"template_code": "incident.created", "audience": "caller", "proof_class": "transactional", "state": "queued"},
        *([{"template_code": "incident.assigned_group", "audience": "assignment_group_dl", "proof_class": "transactional", "state": "queued"}] if group_id else []),
        *([{"template_code": "incident.assigned_you", "audience": "assignee", "proof_class": "transactional", "state": "queued"}] if payload.assignee_id else []),
        *([{"template_code": "incident.major.internal", "audience": "it_leadership", "proof_class": "regulatory_evidence", "state": "queued"}] if payload.major_incident else []),
    ]
    return detail


@router.patch("/{record_id}")
def update_incident(record_id: int, payload: IncidentPatch, principal: Principal = Depends(agent)) -> dict:
    before = _load(record_id)
    patch = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not patch:
        raise HTTPException(422, "no fields to update")

    target_state = patch.get("state")
    if target_state:
        try:
            sm.validate(before, target_state, patch)
        except sm.TransitionError as exc:
            raise HTTPException(422, {"message": str(exc), "missing": exc.missing}) from exc

    now = datetime.now(timezone.utc)
    if target_state:
        if target_state == "in_progress" and before["state"] in ("resolved", "closed"):
            patch["reopen_count"] = (before["reopen_count"] or 0) + 1
            patch["resolved_at"] = None
        if target_state == "in_progress" and before["response_at"] is None:
            patch["response_at"] = now
            patch["response_met"] = (
                None if before["response_due_at"] is None else now <= before["response_due_at"]
            )
        if target_state == "resolved":
            patch["resolved_at"] = now
            patch["resolution_met"] = None if before["resolve_due_at"] is None else now <= before["resolve_due_at"]
        if target_state == "closed":
            patch["closed_at"] = now
    if patch.get("assignee_id") and patch["assignee_id"] != before.get("assignee_id"):
        patch["reassignment_count"] = (before["reassignment_count"] or 0) + 1
    if "priority" in patch and patch["priority"] != before["priority"] and not patch.get("priority_override_reason"):
        raise HTTPException(422, "priority_override_reason is required when changing priority")

    updated = repo.update_record(record_id, patch)
    assert updated is not None
    audit_svc.write_diff(principal.tenant_id, "record", record_id, before, updated, principal.person_id,
                         channel=before.get("channel"))
    if target_state:
        audit_svc.write(principal.tenant_id, "record", record_id, "state_change", field="state",
                        old_value=before["state"], new_value=target_state, actor_id=principal.person_id)
        repo.add_comment(principal.tenant_id, record_id, principal.person_id, "system",
                         f"State changed {before['state']} -> {target_state} by {principal.display_name}.",
                         source="system", is_internal=True)
    detail = repo.record_detail(record_id)
    assert detail is not None
    detail["sla"] = sla_svc.evaluate(detail)
    detail["allowed_transitions"] = sm.allowed(detail["state"])
    return detail


@router.post("/{record_id}/comments", status_code=201)
def add_comment(record_id: int, payload: CommentCreate, principal: Principal = Depends(current_principal)) -> dict:
    record = _load(record_id)
    if payload.kind == "work_note" and not principal.is_agent:
        raise HTTPException(403, "work notes are internal - agent role required")
    is_internal = payload.kind in ("work_note", "system")
    comment = repo.add_comment(
        principal.tenant_id, record_id, principal.person_id, payload.kind, payload.body,
        source=payload.source, is_internal=is_internal, email_message_id=payload.email_message_id,
    )
    audit_svc.write(principal.tenant_id, "record", record_id, "comment_added",
                    field="comment", new_value=payload.kind, actor_id=principal.person_id)
    notification_plan = []
    if payload.kind == "public_comment":
        notification_plan.append({"template_code": "incident.comment_public", "audience": "caller",
                                  "proof_class": "transactional", "state": "queued"})
    return {"comment": comment, "record_number": record["number"], "notification_plan": notification_plan}


@router.post("/{record_id}/take")
def take(record_id: int, principal: Principal = Depends(agent)) -> dict:
    return update_incident(record_id, IncidentPatch(assignee_id=principal.person_id, state="in_progress"), principal)
