# Security Policy

## Reporting a vulnerability
Report privately to the maintainers (do not open a public issue). Include reproduction steps, affected version/commit, and impact.

## Scope of the prototype (Alpha 0.1)
This build is a **prototype**. Known limitations that must not be mistaken for production readiness:
- Authentication is Supabase Auth (email/password + Google) — **no SAML/SCIM**, no enterprise IdP.
- Row-level security is enforced in the application layer, **not** via database RLS.
- No SOC 2 / ISO 27001 / HIPAA / PCI attestation. Do not store regulated data.
- AI features are provider-backed; prompt output is untrusted input until validated.
- No penetration test has been performed.

## Practices in the codebase
- Secrets only via environment (`.env`, git-ignored) or Docker secrets.
- Passwords and tokens are never logged.
- Attachment storage is keyed and access-checked; no public buckets.
- Every state change is written to the audit log with actor, before/after and source channel.
