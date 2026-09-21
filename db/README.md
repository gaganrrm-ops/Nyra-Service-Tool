# db

- `migrations/` — append-only SQL schema migrations, applied in filename order and recorded in `schema_migrations`.
- `seeds/` — demo data, applied after migrations and recorded in `seed_history`.

Apply: `cd apps/api && python -m nyra_api.cli db:migrate && python -m nyra_api.cli db:seed`

Never edit a released migration; add a new numbered file instead.
