# Changelog

All notable changes to Nyra Service Tool. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: SemVer.

## [0.1.0-alpha] - in progress (14-day prototype)

### Added
- Day 1: repository skeleton, Apache-2.0-ready layout, docker-compose stack (postgres:5433, redis, api, web, portal)
- Day 1: database schema v1 — tenants, people, org units, teams with distribution-list addresses, business calendars, SLA policies, taxonomy, services, CIs, records/tasks, incidents, comments, audit, attachments, relationships, KB, CSAT, notification templates/audiences/send-log, saved views, numbering
- Day 1: `nyra` CLI (`db:migrate`, `db:seed`, `db:status`, `doctor`, `smoke`)
- Day 1: demo seed — 2 organisations, IT + HR service desks, L1/L2/L3 + network + applications teams, agents and end users (incl. VIP), taxonomy, P1-P4 SLAs, CIs, tickets in multiple states, KB articles, notification templates

### Known limitations (prototype depth)
- No discovery/service mapping, no SAM reconciliation, no SecOps, no SPM, no mobile, no SAML/SCIM, no vertical packs beyond IT.
