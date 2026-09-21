# Nyra Service Tool

**An open, AI-native ITSM / ITIL 4 service management platform.** Prototype build — this repository is being built in public over a 14-day plan and is labelled **Alpha 0.1** until the day-14 criteria are met.

> Scope honesty: this is a **prototype**. See `docs/SCOPE.md` for exactly what is in and out. Anything not in the scope-in list is not implemented and must not be claimed.

## Status

| Item | State |
|---|---|
| Licence | see `LICENSE` (project intends Apache-2.0 — pending) |
| Version | 0.1.0-alpha |
| Deliverable | 14-day demo core: incident + portal + email + AI |
| Stack | Python 3.12 / FastAPI · Next.js/React · PostgreSQL (Supabase or local) · Docker |

## Quick start

```bash
git clone https://github.com/gaganrrm-ops/Nyra-Service-Tool.git
cd Nyra-Service-Tool
cp .env.example .env          # fill DATABASE_URL (+ Supabase/AI keys later)

# option A - local docker stack (postgres on 5433, redis, api, web, portal)
make up
# option B - use your own Postgres / Supabase
cd apps/api && python -m nyra_api.cli db:migrate && python -m nyra_api.cli db:seed
```

Then:
- API: http://localhost:8000/docs
- Agent workspace: http://localhost:3000
- End-user portal: http://localhost:3001

Verify data landed:
```bash
make status     # row counts per table
make doctor     # environment + db diagnostics
```

## Repository layout

```
apps/api        FastAPI service (records, incidents, people, teams, SLA, notifications, AI)
apps/web        Agent workspace (queues, incident workbench)
apps/portal     End-user portal (submit, track, self-help, CSAT)
db/migrations   SQL schema migrations (append-only)
db/seeds        Demo data
infra           Dockerfiles
docs            Architecture, scope, admin guide, demo script
```

## Documentation
- `docs/ARCHITECTURE.md` — how the system is put together
- `docs/SCOPE.md` — what is in/out of Alpha 0.1 (read before filing issues)
- `docs/DATA-MODEL.md` — the record/incident field model
- `SECURITY.md` — security posture and prototype limitations
- `CHANGELOG.md` — what shipped, day by day

## Contributing
See `CONTRIBUTING.md`. Never commit secrets; every feature ships with a test; no feature gating.
