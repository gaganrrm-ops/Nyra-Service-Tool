# Scope of Alpha 0.1 (14-day demo core)

The full 100% checklist lives outside this repo (spec pack). This file states exactly what the code implements, so no capability is over-claimed.

## In scope (prototype depth)
1. Auth + roles (Supabase Auth: email/password + Google), 5 roles
2. Person / caller model including the `caller (i)` detail bundle
3. Record engine: numbering, states, activity stream, work notes vs public comments, attachments, watchers, relationships, field audit
4. **Incident**: taxonomy, urgency x impact -> priority, assignment, SLA clock, escalation, resolution codes, reopen, major-incident flag
5. Follow-up + auto-close engine (interval, max count, business-calendar aware)
6. **Email**: outbound templates + audience resolver (person, team distribution list, shared mailbox, org slice), send log; inbound IMAP -> ticket; reply -> comment
7. Agent workspace: queues, list, detail, inline edit, take/assign, bulk, macros
8. End-user portal: submit, my tickets, track, comment, attachments, CSAT, KB search, AI self-help
9. Knowledge: article CRUD, draft->publish, search, feedback, AI draft
10. **AI layer**: classify, route suggestion, duplicate detection, summarise, draft reply, KB suggest, sentiment, eval harness, kill switch
11. Reporting: 1 ops dashboard + 5 canned reports + CSV export + daily digest mail
12. Admin console: users, teams + DL addresses, taxonomy, SLA policies, calendars, templates, AI settings
13. API: OpenAPI for all core resources + webhooks
14. Deployment: docker compose on a laptop, public URL via tunnel

## Out of scope (must not be claimed)
Problem management · change/CAB · CMDB depth + discovery + service mapping · asset lifecycle depth · SAM reconciliation · service catalogue + approval chains + RITM · SPM/portfolio · SecOps · SAML/SCIM · mobile/offline · IVR/CTI · visual workflow designer · plugin marketplace · multi-tenant isolation beyond `tenant_id` · i18n beyond English · WCAG audit · performance tuning · Dataverse · vertical packs beyond IT.

## Definition of done (day 14)
1. `git clone` -> `cp .env.example .env` -> `docker compose up` -> working against the user's own Supabase in under 10 minutes, documented.
2. Demo script with no manual SQL: portal submit -> AI triage -> routing -> agent work + notifications -> follow-up -> SLA at-risk -> resolve -> CSAT -> KB published -> dashboard reflects it.
3. Public URL showable to a stranger.
4. Coverage scoreboard with real numbers, generated from the test run.
5. App runs with `AI_ENABLED=false` and the eval harness runs in CI.
