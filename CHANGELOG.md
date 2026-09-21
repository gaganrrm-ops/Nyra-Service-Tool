# Changelog

All notable changes to Nyra Service Tool. Format: [Keep a Changelog](https://keepachangelog.com/); versioning: SemVer.

## [0.1.0-alpha] - in progress (14-day prototype)

### Added
- Day 1: repository skeleton, docker-compose stack (postgres:5433, redis, api, web, portal)
- Day 1: database schema v1 (23 tables)
- Day 1: `nyra` CLI (`db:migrate`, `db:seed`, `db:reset`, `db:status`, `doctor`, `smoke`, `serve`)
- Day 1: demo seed — 2 organisations, IT + HR + Finance + Facilities + plant service desks, L1/L2/L3 + network + applications + security teams with distribution-list addresses, agents and end users (incl. VIP), taxonomy (34 nodes), P1-P4 SLAs, CIs, tickets in multiple states, work notes/public comments/inbound email, KB articles, CSAT, 15 notification templates, 12 audiences, send log, saved views
- Day 1: incident golden path over HTTP — queue with filters/sorting/full-text search, create (numbering → priority matrix → SLA target selection → audit → notification plan), transitions with guards, comments (internal vs public), take/assign
- Day 1: caller `(i)` context bundle (identity, contact incl. caller-ID, employment, access, service context)
- Day 1: business-calendar SLA clocks (holiday aware), ITIL urgency × impact priority matrix, field-level audit diff
- Day 1: 54 tests passing (services unit tests + API integration tests that clean up after themselves)
- Day 1: CI workflow (migrations, idempotency, seed, smoke, tests, no-secrets check)
- Day 1: docs — README, ARCHITECTURE, DATA-MODEL, SCOPE, DEV-POSTGRES, SECURITY, CONTRIBUTING

### Verified on this machine (not claimed, measured)
- PostgreSQL 16.13 (throwaway cluster, port 5434, no Docker daemon available)
- `db:migrate` applied 0001_init.sql (23 tables) cleanly and is idempotent on re-run
- `db:seed` idempotent; `smoke` = ALL CHECKS PASSED (16 checks)
- `pytest` = 54 passed
- `GET /health`, `/api/v1/meta/summary`, `/api/v1/incidents`, `/api/v1/people/20/context` exercised over real HTTP

### Known limitations (prototype depth)
- No discovery/service mapping, no SAM reconciliation, no SecOps, no SPM, no mobile, no SAML/SCIM, no vertical packs beyond IT
- Notifications are **planned and logged, not sent** — SMTP/IMAP transport lands day 8-9
- `record.sla_state` is stored, not continuously recomputed (live evaluation exists per record in the API)
- Authentication in `AUTH_MODE=dev` trusts the `X-Nyra-Person-Id` header for local development; Supabase JWT verification exists but is untested against a live project
- `LICENSE` is currently the Unlicense text committed with the repository; the project intends Apache-2.0 and this must be settled before the public launch

