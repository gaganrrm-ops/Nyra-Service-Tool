"""Request/response models. Response models are permissive on purpose: the underlying row dict is returned so the
UI can use every column, while request models are strict."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

RecordType = Literal["incident", "problem", "change", "request", "ritm", "task", "problem_task", "change_task", "catalog_task"]
Channel = Literal["portal", "email", "phone", "chat", "walk_up", "api", "monitoring", "agent", "teams", "whatsapp", "system"]


class IncidentCreate(BaseModel):
    short_description: str = Field(min_length=5, max_length=250)
    description: str | None = None
    caller_id: int
    channel: Channel = "portal"
    urgency: int = Field(default=3, ge=1, le=3)
    impact: int = Field(default=3, ge=1, le=3)
    category_id: int | None = None
    subcategory_id: int | None = None
    service_id: int | None = None
    ci_id: int | None = None
    assignment_group_id: int | None = None
    assignee_id: int | None = None
    priority_override: int | None = Field(default=None, ge=1, le=5)
    priority_override_reason: str | None = None
    major_incident: bool = False
    tags: list[str] = Field(default_factory=list)
    work_notes: str | None = None
    parent_id: int | None = None
    followup: dict[str, Any] | None = None

    @field_validator("short_description")
    @classmethod
    def _strip(cls, v: str) -> str:
        return " ".join(v.split())


class IncidentPatch(BaseModel):
    state: str | None = None
    state_reason: str | None = None
    assignment_group_id: int | None = None
    assignee_id: int | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    priority_override_reason: str | None = None
    urgency: int | None = Field(default=None, ge=1, le=3)
    impact: int | None = Field(default=None, ge=1, le=3)
    category_id: int | None = None
    subcategory_id: int | None = None
    service_id: int | None = None
    ci_id: int | None = None
    major_incident: bool | None = None
    escalation: bool | None = None
    escalation_reason: str | None = None
    quality_miss: bool | None = None
    on_hold_reason: str | None = None
    workaround: str | None = None
    resolution_notes: str | None = None
    resolution_code: str | None = None
    root_cause_code: str | None = None
    followup: dict[str, Any] | None = None
    autoclose: dict[str, Any] | None = None
    short_description: str | None = None
    description: str | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    kind: Literal["work_note", "public_comment", "email_in", "email_out", "system"] = "work_note"
    source: str = "agent"
    email_message_id: str | None = None


class PrincipalOut(BaseModel):
    person_id: int
    tenant_id: int
    display_name: str
    roles: list[str]
    auth_mode: str
    server_time: datetime
