"""Integration tests against a seeded database. Skipped when no database is reachable.

These tests exercise the day-1 golden path over real HTTP (TestClient): queue -> create -> transition -> comment,
including the ITIL priority matrix, the SLA clock, RBAC and the audit trail.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nyra_api.main import app
from tests.conftest import requires_db

pytestmark = requires_db

AGENT_HEADERS = {"X-Nyra-Person-Id": "3"}      # Arjun Menon, agent_l1
LEAD_HEADERS = {"X-Nyra-Person-Id": "2"}       # Priya Sharma, team_lead
END_USER_HEADERS = {"X-Nyra-Person-Id": "21"}  # Kiran Patel, end_user


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_health_reports_database_connected(client: TestClient):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database_connected"] is True


def test_root_advertises_docs(client: TestClient):
    assert client.get("/").json()["docs"] == "/docs"


def test_openapi_schema_is_published(client: TestClient):
    schema = client.get("/openapi.json").json()
    for path in ("/api/v1/incidents", "/api/v1/people/{person_id}/context", "/api/v1/kb", "/api/v1/audit"):
        assert path in schema["paths"], path


def test_meta_summary_has_counts_and_queues(client: TestClient):
    body = client.get("/api/v1/meta/summary", headers=AGENT_HEADERS).json()
    assert body["tenant"]["slug"] == "nyra-demo"
    assert body["counts"]["incidents"] >= 8
    assert body["next_number_preview"]["incident"].startswith("INC")


def test_priority_matrix_endpoint_exposes_nine_cells(client: TestClient):
    body = client.get("/api/v1/meta/priorities").json()
    assert len(body["matrix"]) == 9


def test_teams_expose_distribution_list_and_load(client: TestClient):
    teams = client.get("/api/v1/teams", headers=LEAD_HEADERS).json()["teams"]
    l1 = next(t for t in teams if t["code"] == "SD-L1")
    assert l1["email"] == "servicedesk-l1@example.com"
    assert l1["mailbox_mode"] == "relay"
    assert "open_count" in l1


def test_caller_context_returns_all_i_popover_sections(client: TestClient):
    ctx = client.get("/api/v1/people/20/context", headers=AGENT_HEADERS).json()
    assert set(ctx) == {"identity", "contact", "employment", "access", "service_context"}
    assert ctx["service_context"]["is_vip"] is True
    assert ctx["contact"]["caller_id"] == "+918040101001"
    assert ctx["employment"]["manager"]


def test_caller_context_requires_agent_role(client: TestClient):
    assert client.get("/api/v1/people/20/context", headers=END_USER_HEADERS).status_code == 403


def test_queue_is_ordered_by_priority_then_due(client: TestClient):
    rows = client.get("/api/v1/incidents", params={"open_only": True}, headers=AGENT_HEADERS).json()["incidents"]
    assert rows, "expected open incidents"
    assert [r["priority"] for r in rows] == sorted(r["priority"] for r in rows)


def test_queue_filters_major_incidents(client: TestClient):
    rows = client.get("/api/v1/incidents", params={"major_incident": True}, headers=AGENT_HEADERS).json()["incidents"]
    assert len(rows) == 1 and rows[0]["number"] == "INC0000002"


def test_full_text_search_on_queue(client: TestClient):
    rows = client.get("/api/v1/incidents", params={"q": "invoice"}, headers=AGENT_HEADERS).json()["incidents"]
    assert any("invoice" in r["short_description"].lower() for r in rows)


def test_detail_includes_comments_sla_transitions_and_notification_plan(client: TestClient):
    body = client.get("/api/v1/incidents/1", headers=AGENT_HEADERS).json()
    for key in ("comments", "sla", "allowed_transitions", "notification_log", "audit", "children"):
        assert key in body
    assert len(body["comments"]) >= 3
    assert body["sla"]["sla_state"] in ("ok", "at_risk", "breached")
    assert "in_progress" in body["allowed_transitions"] or body["state"] == "in_progress"


def test_create_incident_applies_priority_matrix_and_sla(client: TestClient):
    payload = {
        "short_description": "pytest - laptop will not boot after BIOS update",
        "description": "Created by the automated test suite.",
        "caller_id": 23,
        "channel": "phone",
        "urgency": 1,
        "impact": 1,
        "category_id": 1,
        "subcategory_id": 2,
        "service_id": 4,
        "assignment_group_id": 2,
        "tags": ["pytest"],
    }
    body = client.post("/api/v1/incidents", json=payload, headers=AGENT_HEADERS).json()
    assert body["number"].startswith("INC")
    assert body["priority"] == 1                      # urgency 1 x impact 1
    assert body["resolve_due_at"] is not None          # SLA clock started
    assert body["sla_policy_id"] is not None
    assert body["notification_plan"][0]["template_code"] == "incident.created"
    assert any(p["audience"] == "assignment_group_dl" for p in body["notification_plan"])

    # the audit trail must record creation
    audit = client.get("/api/v1/audit", params={"entity_type": "record", "entity_id": body["id"]}, headers=AGENT_HEADERS).json()
    assert any(e["action"] == "created" for e in audit["entries"])


def test_create_incident_routes_by_category_default_team(client: TestClient):
    body = client.post(
        "/api/v1/incidents",
        json={"short_description": "pytest - vpn token expired", "caller_id": 23, "channel": "portal", "urgency": 2, "impact": 2, "category_id": 8, "tags": ["pytest"]},
        headers=AGENT_HEADERS,
    ).json()
    assert body["assignment_group_id"] == 3  # Network & Connectivity L2 is the default team for the Network category


def test_create_incident_rejects_unknown_caller(client: TestClient):
    resp = client.post("/api/v1/incidents", json={"short_description": "pytest - bad caller", "caller_id": 99999, "tags": ["pytest"]}, headers=AGENT_HEADERS)
    assert resp.status_code == 422


def test_end_user_cannot_create_incident_as_agent(client: TestClient):
    resp = client.post("/api/v1/incidents", json={"short_description": "pytest - end user attempt", "caller_id": 21, "tags": ["pytest"]}, headers=END_USER_HEADERS)
    assert resp.status_code == 403


def test_transition_resolved_requires_resolution_notes(client: TestClient):
    created = client.post(
        "/api/v1/incidents",
        json={"short_description": "pytest - transition guard", "caller_id": 23, "assignment_group_id": 1, "tags": ["pytest"]},
        headers=AGENT_HEADERS,
    ).json()
    client.post(f"/api/v1/incidents/{created['id']}/take", headers=AGENT_HEADERS)  # new -> in_progress is the legal path
    resp = client.patch(f"/api/v1/incidents/{created['id']}", json={"state": "resolved"}, headers=AGENT_HEADERS)
    assert resp.status_code == 422
    assert "resolution_notes" in resp.json()["detail"]["missing"]


def test_transition_with_notes_resolves_and_sets_metrics(client: TestClient):
    created = client.post(
        "/api/v1/incidents",
        json={"short_description": "pytest - resolve path", "caller_id": 23, "assignment_group_id": 1, "tags": ["pytest"]},
        headers=AGENT_HEADERS,
    ).json()
    client.post(f"/api/v1/incidents/{created['id']}/take", headers=AGENT_HEADERS)
    body = client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={"state": "resolved", "resolution_notes": "Replaced the docking station under warranty.", "resolution_code": "FIXED_HARDWARE"},
        headers=AGENT_HEADERS,
    ).json()
    assert body["state"] == "resolved"
    assert body["resolved_at"] is not None
    assert body["resolution_met"] in (True, False)


def test_illegal_transition_rejected(client: TestClient):
    created = client.post(
        "/api/v1/incidents",
        json={"short_description": "pytest - illegal jump", "caller_id": 23, "assignment_group_id": 1, "tags": ["pytest"]},
        headers=AGENT_HEADERS,
    ).json()
    resp = client.patch(f"/api/v1/incidents/{created['id']}", json={"state": "closed"}, headers=AGENT_HEADERS)
    assert resp.status_code == 422


def test_take_assigns_to_current_agent(client: TestClient):
    created = client.post(
        "/api/v1/incidents",
        json={"short_description": "pytest - take flow", "caller_id": 23, "assignment_group_id": 1, "tags": ["pytest"]},
        headers=AGENT_HEADERS,
    ).json()
    body = client.post(f"/api/v1/incidents/{created['id']}/take", headers=AGENT_HEADERS).json()
    assert body["assignee_id"] == 3
    assert body["state"] == "in_progress"


def test_priority_change_requires_reason(client: TestClient):
    created = client.post(
        "/api/v1/incidents", json={"short_description": "pytest - priority guard", "caller_id": 23, "tags": ["pytest"]}, headers=AGENT_HEADERS
    ).json()
    resp = client.patch(f"/api/v1/incidents/{created['id']}", json={"priority": 1}, headers=AGENT_HEADERS)
    assert resp.status_code == 422
    ok = client.patch(
        f"/api/v1/incidents/{created['id']}",
        json={"priority": 1, "priority_override_reason": "executive escalation"},
        headers=AGENT_HEADERS,
    )
    assert ok.status_code == 200


def test_work_notes_are_internal_only(client: TestClient):
    created = client.post(
        "/api/v1/incidents", json={"short_description": "pytest - work note guard", "caller_id": 23, "tags": ["pytest"]}, headers=AGENT_HEADERS
    ).json()
    resp = client.post(f"/api/v1/incidents/{created['id']}/comments", json={"body": "internal note", "kind": "work_note"}, headers=END_USER_HEADERS)
    assert resp.status_code == 403


def test_public_comment_queues_caller_notification(client: TestClient):
    created = client.post(
        "/api/v1/incidents", json={"short_description": "pytest - public comment", "caller_id": 23, "tags": ["pytest"]}, headers=AGENT_HEADERS
    ).json()
    body = client.post(
        f"/api/v1/incidents/{created['id']}/comments",
        json={"body": "We are testing the update path.", "kind": "public_comment"},
        headers=AGENT_HEADERS,
    ).json()
    assert body["notification_plan"][0]["template_code"] == "incident.comment_public"


def test_kb_search_and_feedback(client: TestClient):
    hits = client.get("/api/v1/kb", params={"q": "vpn", "scope": "portal"}, headers=AGENT_HEADERS).json()
    assert hits["count"] >= 1
    article_id = hits["articles"][0]["id"]
    assert client.get(f"/api/v1/kb/{article_id}", headers=AGENT_HEADERS).status_code == 200
    assert client.post(f"/api/v1/kb/{article_id}/feedback", params={"helpful": True}, headers=AGENT_HEADERS).status_code == 201


def test_notification_templates_and_audiences_seeded(client: TestClient):
    templates = client.get("/api/v1/notifications/templates", headers=LEAD_HEADERS).json()
    codes = {t["code"] for t in templates["templates"]}
    assert {"incident.created", "incident.assigned_group", "incident.major.internal"} <= codes
    audiences = client.get("/api/v1/notifications/audiences", headers=LEAD_HEADERS).json()
    kinds = {a["audience_type"] for a in audiences["audiences"]}
    assert {"person", "team_dl", "shared_mailbox", "org_slice"} <= kinds


def test_saved_view_runs_and_returns_records(client: TestClient):
    views = client.get("/api/v1/meta/views", headers=LEAD_HEADERS).json()
    major = next(v for v in views if v["name"] == "Major incidents")
    body = client.get(f"/api/v1/meta/views/{major['id']}/records", headers=LEAD_HEADERS).json()
    assert body["count"] >= 1
    assert body["records"][0]["major_incident"] is True


def test_unknown_incident_returns_404(client: TestClient):
    assert client.get("/api/v1/incidents/99999", headers=AGENT_HEADERS).status_code == 404
