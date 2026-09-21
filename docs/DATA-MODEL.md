# Data model (record + incident)

## Record (base of every ticket-like object)
`record` holds incidents, problems, changes, requests, RITMs and tasks in one table with a `type` discriminator. Rationale: every ITSM record shares ~80% of its fields and the same lifecycle machinery (activity, SLA, notifications, relationships, audit). Splitting them into separate tables duplicates that machinery six times.

Shared columns: `tenant_id, number, type, parent_id, root_id, short_description, description, state, opened_by, opened_at, caller_id, channel, assignment_group_id, assignee_id, priority, urgency, impact, severity, category_id, subcategory_id, service_id, ci_id, location_id, department_id, company_id, major_incident, escalation, quality_miss, reopen_count, reassignment_count, workaround, resolution_notes, resolution_code, root_cause_code, hold_reason, sla_response_met, sla_resolution_met, followup, autoclose, ai, ext, created_by, updated_by, resolved_at, closed_at, due_at, deleted_at`.

JSONB extension points:
- `followup` = `{enabled, interval_hours, max_count, sent_count, last_sent_at, no_response_action}`
- `autoclose` = `{enabled, after_followups, business_days, reopen_window_hours}`
- `ai` = `{category_suggestion, confidence, summary, sentiment, duplicate_of, model, trace_id, tier}`

## States (incident)
`new -> in_progress -> on_hold <-> in_progress -> resolved -> closed` plus `reopened -> in_progress`, `cancelled`.
Transitions, guards, required fields and the audit entry per transition live in `services/state_machine.py` (day 6).

## Priority (ITIL)
`priority = f(impact, urgency)` via the matrix in `services/priority.py`, overridable per tenant, with an override reason captured in the audit log.

## Caller detail bundle (`GET /api/v1/people/{id}/context`)
Identity · contact (incl. caller-ID/ANI with match confidence) · employment (manager, department, grade, cost centre) · access (roles, teams, access level) · assets · service context (VIP flag, entitlements, open-ticket count, CSAT average) · consents. This powers the `(i)` popover on every record form.

## Notifications
`notification_template` (per event, per locale, versioned) · `notification_audience` (person, team distribution list, shared mailbox, distribution list, org slice, role, on-call, watchlist, external, system + expansion mode + privacy class) · `notification_send_log` (proof: template version, resolved audience, delivery state, proof class, message-id, initiator).
