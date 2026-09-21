"""All SQL for the API lives here. Parameterised statements only - user input is never interpolated."""

from __future__ import annotations

from typing import Any

from . import db

PERSON_COLS = """id, tenant_id, party_type, user_name, first_name, last_name, display_name, email, phone, mobile,
                 caller_id, job_title, employee_id, department_id, company_id, location_id, cost_center, grade,
                 worker_type, manager_id, roles, access_level, team_id, is_vip, vip_reason, language, timezone,
                 is_active, hire_date"""

RECORD_COLS = """id, tenant_id, number, type, parent_id, root_id, short_description, description, state, state_reason,
                 opened_by, opened_at, caller_id, channel, assignment_group_id, assignee_id, created_by, updated_by,
                 priority, urgency, impact, severity, category_id, subcategory_id, service_id, ci_id, location_id,
                 department_id, company_id, major_incident, escalation, quality_miss, security_flag, regulatory_flag,
                 on_hold_reason, reopen_count, reassignment_count, first_call_resolution, workaround,
                 resolution_notes, resolution_code, root_cause_code, response_at, response_due_at, resolve_due_at,
                 resolved_at, resolution_met, closed_at, due_at, sla_state, sla_policy_id, followup, autoclose, ai,
                 tags, created_at, updated_at"""


# ------------------------------------------------------------------ tenant / people
def default_tenant() -> dict[str, Any] | None:
    from .config import settings

    return db.query_one("select * from tenant where slug=%s", (settings().default_tenant_slug,)) or db.query_one(
        "select * from tenant order by id limit 1"
    )


def default_principal_id() -> int:
    row = db.query_one("select id from person where 'admin' = any(roles) order by id limit 1")
    return int(row["id"]) if row else 1


def get_person(person_id: int) -> dict[str, Any] | None:
    return db.query_one("select " + PERSON_COLS + " from person where id=%s", (person_id,))


def get_person_by_email(email: str) -> dict[str, Any] | None:
    return db.query_one("select " + PERSON_COLS + " from person where lower(email)=lower(%s)", (email,))


def list_people(
    tenant_id: int,
    *,
    search: str | None = None,
    active: bool | None = None,
    vip: bool | None = None,
    department_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    where = ["p.tenant_id = %(tenant_id)s"]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}
    if search:
        where.append("(p.display_name ilike %(q)s or p.email ilike %(q)s or p.employee_id ilike %(q)s)")
        params["q"] = "%" + search + "%"
    if active is not None:
        where.append("p.is_active = %(active)s")
        params["active"] = active
    if vip is not None:
        where.append("p.is_vip = %(vip)s")
        params["vip"] = vip
    if department_id:
        where.append("p.department_id = %(department_id)s")
        params["department_id"] = department_id
    clause = " and ".join(where)
    return db.query(
        """
        select p.id, p.display_name, p.email, p.phone, p.mobile, p.job_title, p.party_type, p.roles,
               p.access_level, p.is_vip, p.is_active, p.team_id, p.department_id, p.location_id,
               d.name as department_name, l.name as location_name, t.name as team_name
        from person p
        left join org_unit d on d.id = p.department_id
        left join org_unit l on l.id = p.location_id
        left join team t on t.id = p.team_id
        where """ + clause + """
        order by p.display_name
        limit %(limit)s offset %(offset)s
        """,
        params,
    )


def person_context(person_id: int) -> dict[str, Any]:
    """The data behind the (i) popover on every record form."""
    person = db.query_one(
        """
        select p.*, m.display_name as manager_name, m.email as manager_email,
               d.name as department_name, c.name as company_name, l.name as location_name,
               t.name as team_name, t.email as team_email
        from person p
        left join person m on m.id = p.manager_id
        left join org_unit d on d.id = p.department_id
        left join org_unit c on c.id = p.company_id
        left join org_unit l on l.id = p.location_id
        left join team t on t.id = p.team_id
        where p.id = %s
        """,
        (person_id,),
    )
    if not person:
        return {}
    teams = db.query(
        """
        select t.id, t.name, t.email, t.domain, t.tier, tm.team_role
        from team_member tm join team t on t.id = tm.team_id
        where tm.person_id = %s order by t.name
        """,
        (person_id,),
    )
    open_tickets = db.query_one(
        """
        select count(*) filter (where state not in ('closed','cancelled','resolved')) as open_count,
               count(*) filter (where major_incident) as major_count,
               max(created_at) as last_activity
        from record where caller_id = %s
        """,
        (person_id,),
    )
    csat = db.query_one(
        "select round(avg(score)::numeric, 2) as avg_score, count(*) as responses from csat_survey where person_id=%s",
        (person_id,),
    )
    recent = db.query(
        """
        select number, type, short_description, state, priority, created_at
        from record where caller_id = %s order by created_at desc limit 5
        """,
        (person_id,),
    )
    return {
        "identity": {
            "id": person["id"],
            "display_name": person["display_name"],
            "party_type": person["party_type"],
            "user_name": person["user_name"],
            "employee_id": person["employee_id"],
            "job_title": person["job_title"],
            "worker_type": person["worker_type"],
            "hire_date": person["hire_date"],
            "is_active": person["is_active"],
        },
        "contact": {
            "email": person["email"],
            "personal_email": person["personal_email"],
            "phone": person["phone"],
            "mobile": person["mobile"],
            "caller_id": person["caller_id"],
            "address": person["address"],
        },
        "employment": {
            "manager": person["manager_name"],
            "manager_email": person["manager_email"],
            "department": person["department_name"],
            "company": person["company_name"],
            "location": person["location_name"],
            "cost_center": person["cost_center"],
            "grade": person["grade"],
            "team": person["team_name"],
            "team_email": person["team_email"],
        },
        "access": {
            "roles": person["roles"],
            "access_level": person["access_level"],
            "child_teams": [{"name": t["name"], "email": t["email"], "role": t["team_role"]} for t in teams],
        },
        "service_context": {
            "is_vip": person["is_vip"],
            "vip_reason": person["vip_reason"],
            "language": person["language"],
            "timezone": person["timezone"],
            "consents": person["consents"],
            "open_tickets": (open_tickets or {}).get("open_count"),
            "major_incidents": (open_tickets or {}).get("major_count"),
            "last_activity": (open_tickets or {}).get("last_activity"),
            "csat_average": (csat or {}).get("avg_score"),
            "csat_responses": (csat or {}).get("responses"),
            "recent_records": recent,
        },
    }


# ------------------------------------------------------------------ org / teams / taxonomy
def list_org_units(tenant_id: int, kind: str | None = None) -> list[dict[str, Any]]:
    if kind:
        return db.query("select * from org_unit where tenant_id=%s and kind=%s order by name", (tenant_id, kind))
    return db.query("select * from org_unit where tenant_id=%s order by kind, name", (tenant_id,))


def list_teams(tenant_id: int, domain: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = [tenant_id]
    sql = """
        select t.id, t.name, t.code, t.tier, t.domain, t.email, t.mailbox_mode, t.shared_mailbox, t.skills,
               t.description, t.active, t.calendar_id, t.escalation_team_id, t.default_sla_policy_id,
               m.display_name as manager_name,
               (select count(*) from team_member tm where tm.team_id = t.id) as member_count,
               (select count(*) from record r where r.assignment_group_id = t.id
                  and r.state not in ('closed','cancelled','resolved')) as open_count
        from team t left join person m on m.id = t.manager_id
        where t.tenant_id = %s
    """
    if domain:
        sql += " and t.domain = %s"
        params.append(domain)
    sql += " order by t.domain, t.tier nulls last, t.name"
    return db.query(sql, params)


def team_members(team_id: int) -> list[dict[str, Any]]:
    return db.query(
        """
        select p.id, p.display_name, p.email, p.is_vip, tm.team_role, tm.capacity
        from team_member tm join person p on p.id = tm.person_id
        where tm.team_id = %s order by tm.team_role, p.display_name
        """,
        (team_id,),
    )


def list_taxonomy(tenant_id: int, domain: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = [tenant_id]
    sql = """
        select x.*, p.name as parent_name, t.name as default_team_name
        from taxonomy x left join taxonomy p on p.id = x.parent_id
        left join team t on t.id = x.default_team_id
        where x.tenant_id = %s
    """
    if domain:
        sql += " and x.domain = %s"
        params.append(domain)
    sql += " order by x.domain, x.kind, p.name nulls first, x.name"
    return db.query(sql, params)


def list_services(tenant_id: int) -> list[dict[str, Any]]:
    return db.query(
        """
        select s.*, o.display_name as owner_name, t.name as support_team_name
        from service s left join person o on o.id = s.owner_id
        left join team t on t.id = s.support_team_id
        where s.tenant_id=%s and s.active order by s.criticality, s.name
        """,
        (tenant_id,),
    )


def list_sla_policies(tenant_id: int) -> list[dict[str, Any]]:
    return db.query("select * from sla_policy where tenant_id=%s and active order by applies_to, name", (tenant_id,))


def list_saved_views(tenant_id: int, person_id: int | None = None) -> list[dict[str, Any]]:
    return db.query(
        """
        select * from saved_view
        where tenant_id=%s and (shared or owner_id = %s or %s is null)
        order by shared desc, name
        """,
        (tenant_id, person_id, person_id),
    )


def counts(tenant_id: int) -> dict[str, Any]:
    row = db.query_one(
        """
        select
          (select count(*) from record where tenant_id=%(t)s) as records,
          (select count(*) from record where tenant_id=%(t)s and type='incident') as incidents,
          (select count(*) from record where tenant_id=%(t)s and state not in ('closed','cancelled','resolved')) as open_records,
          (select count(*) from record where tenant_id=%(t)s and sla_state='at_risk') as at_risk,
          (select count(*) from record where tenant_id=%(t)s and sla_state='breached') as breached,
          (select count(*) from record where tenant_id=%(t)s and major_incident) as major,
          (select count(*) from person where tenant_id=%(t)s) as people,
          (select count(*) from person where tenant_id=%(t)s and is_vip) as vip_people,
          (select count(*) from team where tenant_id=%(t)s) as teams,
          (select count(*) from kb_article where tenant_id=%(t)s) as kb_articles,
          (select count(*) from notification_template where tenant_id=%(t)s) as notification_templates,
          (select count(*) from notification_send_log where tenant_id=%(t)s) as notification_sends,
          (select count(*) from saved_view where tenant_id=%(t)s) as saved_views,
          (select count(*) from audit_log where tenant_id=%(t)s) as audit_rows
        """,
        {"t": tenant_id},
    )
    return row or {}


# ------------------------------------------------------------------ records
def get_record(record_id: int) -> dict[str, Any] | None:
    return db.query_one("select " + RECORD_COLS + " from record where id=%s and deleted_at is null", (record_id,))


def get_record_by_number(number: str) -> dict[str, Any] | None:
    return db.query_one("select " + RECORD_COLS + " from record where number=%s and deleted_at is null", (number,))


SORTS = {
    "priority": "r.priority asc, r.resolve_due_at asc nulls last",
    "opened_desc": "r.opened_at desc",
    "opened_asc": "r.opened_at asc",
    "due": "r.resolve_due_at asc nulls last",
    "updated_desc": "r.updated_at desc",
}


def list_records(
    tenant_id: int,
    *,
    type_: str | None = "incident",
    state: list[str] | None = None,
    assignee_id: int | None = None,
    unassigned: bool | None = None,
    assignment_group_id: int | None = None,
    priority: list[int] | None = None,
    sla_state: list[str] | None = None,
    major_incident: bool | None = None,
    open_only: bool | None = None,
    service_id: int | None = None,
    caller_id: int | None = None,
    search: str | None = None,
    sort: str = "priority",
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    where = ["r.tenant_id = %(tenant_id)s", "r.deleted_at is null"]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}
    if type_:
        where.append("r.type = %(type)s")
        params["type"] = type_
    if state:
        where.append("r.state = any(%(state)s)")
        params["state"] = state
    if open_only:
        where.append("r.state not in ('closed','cancelled','resolved')")
    if assignee_id:
        where.append("r.assignee_id = %(assignee_id)s")
        params["assignee_id"] = assignee_id
    if unassigned:
        where.append("r.assignee_id is null")
    if assignment_group_id:
        where.append("r.assignment_group_id = %(group)s")
        params["group"] = assignment_group_id
    if priority:
        where.append("r.priority = any(%(priority)s)")
        params["priority"] = priority
    if sla_state:
        where.append("r.sla_state = any(%(sla_state)s)")
        params["sla_state"] = sla_state
    if major_incident is not None:
        where.append("r.major_incident = %(major)s")
        params["major"] = major_incident
    if service_id:
        where.append("r.service_id = %(service)s")
        params["service"] = service_id
    if caller_id:
        where.append("r.caller_id = %(caller)s")
        params["caller"] = caller_id
    if search:
        where.append(
            "to_tsvector('english', r.short_description || ' ' || coalesce(r.description,''))"
            " @@ plainto_tsquery('english', %(q)s)"
        )
        params["q"] = search
    clause = " and ".join(where)
    order = SORTS.get(sort, SORTS["priority"])
    return db.query(
        """
        select r.id, r.number, r.type, r.short_description, r.state, r.priority, r.urgency, r.impact, r.channel,
               r.opened_at, r.updated_at, r.resolve_due_at, r.response_due_at, r.sla_state, r.major_incident,
               r.escalation, r.assignment_group_id, r.assignee_id, r.caller_id, r.category_id, r.subcategory_id,
               r.service_id, r.ci_id, r.ai, r.tags,
               g.name as assignment_group, a.display_name as assignee_name,
               c.display_name as caller_name, c.is_vip as caller_vip,
               cat.name as category, sub.name as subcategory, s.name as service, ci.name as ci_name,
               case when r.resolve_due_at is null then null
                    else round(extract(epoch from (r.resolve_due_at - now()))/60)::int end as sla_remaining_minutes
        from record r
        left join team g on g.id = r.assignment_group_id
        left join person a on a.id = r.assignee_id
        left join person c on c.id = r.caller_id
        left join taxonomy cat on cat.id = r.category_id
        left join taxonomy sub on sub.id = r.subcategory_id
        left join service s on s.id = r.service_id
        left join ci on ci.id = r.ci_id
        where """ + clause + """
        order by """ + order + """
        limit %(limit)s offset %(offset)s
        """,
        params,
    )


def record_detail(record_id: int) -> dict[str, Any] | None:
    row = db.query_one(
        """
        select r.*, g.name as assignment_group, g.email as assignment_group_email,
               a.display_name as assignee_name, a.email as assignee_email,
               c.display_name as caller_name, c.email as caller_email, c.is_vip as caller_vip,
               cat.name as category, sub.name as subcategory, s.name as service, s.criticality as service_criticality,
               ci.name as ci_name, ci.ci_class, p.number as parent_number, sp.name as sla_policy_name
        from record r
        left join team g on g.id = r.assignment_group_id
        left join person a on a.id = r.assignee_id
        left join person c on c.id = r.caller_id
        left join taxonomy cat on cat.id = r.category_id
        left join taxonomy sub on sub.id = r.subcategory_id
        left join service s on s.id = r.service_id
        left join ci on ci.id = r.ci_id
        left join record p on p.id = r.parent_id
        left join sla_policy sp on sp.id = r.sla_policy_id
        where r.id = %s and r.deleted_at is null
        """,
        (record_id,),
    )
    if not row:
        return None
    row["comments"] = list_comments(record_id)
    row["children"] = db.query(
        "select id, number, type, short_description, state, assignee_id from record where parent_id=%s order by id",
        (record_id,),
    )
    row["relationships"] = db.query(
        """
        select rr.relation, r2.id, r2.number, r2.type, r2.short_description, r2.state
        from record_relationship rr join record r2 on r2.id = rr.related_id
        where rr.record_id = %s order by rr.relation
        """,
        (record_id,),
    )
    row["attachments"] = db.query(
        "select id, filename, content_type, size_bytes, driver, created_at from attachment where record_id=%s order by id",
        (record_id,),
    )
    row["notification_log"] = db.query(
        """
        select template_code, template_version, audience_code, recipients_count, delivery_state, proof_class, created_at
        from notification_send_log where record_id=%s order by created_at desc limit 25
        """,
        (record_id,),
    )
    row["audit"] = db.query(
        """
        select action, field, old_value, new_value, actor_id, actor_type, at from audit_log
        where entity_type='record' and entity_id=%s order by at desc limit 50
        """,
        (record_id,),
    )
    return row


def list_comments(record_id: int) -> list[dict[str, Any]]:
    return db.query(
        """
        select c.id, c.kind, c.body, c.source, c.is_internal, c.created_at, p.display_name as author_name
        from record_comment c left join person p on p.id = c.author_id
        where c.record_id=%s order by c.created_at
        """,
        (record_id,),
    )


def create_record(payload: dict[str, Any]) -> dict[str, Any] | None:
    cols = ", ".join(payload.keys())
    placeholders = ", ".join("%(" + k + ")s" for k in payload)
    return db.execute_returning("insert into record (" + cols + ") values (" + placeholders + ") returning *", payload)


def update_record(record_id: int, patch: dict[str, Any]) -> dict[str, Any] | None:
    if not patch:
        return get_record(record_id)
    assignments = ", ".join(k + " = %(" + k + ")s" for k in patch)
    params = dict(patch)
    params["id"] = record_id
    return db.execute_returning(
        "update record set " + assignments + ", updated_at = now() where id = %(id)s returning *", params
    )


def add_comment(
    tenant_id: int,
    record_id: int,
    author_id: int | None,
    kind: str,
    body: str,
    source: str = "agent",
    is_internal: bool = True,
    email_message_id: str | None = None,
) -> dict[str, Any] | None:
    return db.execute_returning(
        """
        insert into record_comment (tenant_id, record_id, author_id, kind, body, source, is_internal, email_message_id)
        values (%s,%s,%s,%s,%s,%s,%s,%s) returning *
        """,
        (tenant_id, record_id, author_id, kind, body, source, is_internal, email_message_id),
    )


# ------------------------------------------------------------------ knowledge
def search_kb(
    tenant_id: int, q: str | None = None, *, visibility: list[str] | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}
    where = ["k.tenant_id = %(tenant_id)s", "k.state = 'published'"]
    if visibility:
        where.append("k.visibility = any(%(visibility)s)")
        params["visibility"] = visibility
    if q:
        where.append(
            "to_tsvector('english', k.title || ' ' || coalesce(k.summary,'') || ' ' || k.body)"
            " @@ plainto_tsquery('english', %(q)s)"
        )
        params["q"] = q
    clause = " and ".join(where)
    return db.query(
        """
        select k.id, k.number, k.title, k.summary, k.visibility, k.hit_count, k.helpful_count, k.not_helpful_count,
               k.tags, k.published_at, t.name as category_name
        from kb_article k left join taxonomy t on t.id = k.category_id
        where """ + clause + """
        order by (k.helpful_count - k.not_helpful_count) desc, k.hit_count desc
        limit %(limit)s
        """,
        params,
    )


def get_kb(article_id: int) -> dict[str, Any] | None:
    return db.query_one("select * from kb_article where id=%s", (article_id,))


# ------------------------------------------------------------------ audit
def list_audit(
    tenant_id: int, *, entity_type: str | None = None, entity_id: int | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    where = ["a.tenant_id = %(tenant_id)s"]
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}
    if entity_type:
        where.append("a.entity_type = %(entity_type)s")
        params["entity_type"] = entity_type
    if entity_id:
        where.append("a.entity_id = %(entity_id)s")
        params["entity_id"] = entity_id
    clause = " and ".join(where)
    return db.query(
        """
        select a.id, a.entity_type, a.entity_id, a.action, a.field, a.old_value, a.new_value, a.actor_type,
               a.channel, a.at, p.display_name as actor_name
        from audit_log a left join person p on p.id = a.actor_id
        where """ + clause + """
        order by a.at desc limit %(limit)s
        """,
        params,
    )


def seed_state() -> dict[str, Any]:
    return {
        "migrations": db.query("select filename, applied_at from schema_migrations order by filename"),
        "seeds": db.query("select filename, applied_at from seed_history order by filename"),
    }
