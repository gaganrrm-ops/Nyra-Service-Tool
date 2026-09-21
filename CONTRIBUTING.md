# Contributing to Nyra Service Tool

Thanks for helping build an open, AI-native ITSM platform.

## Ground rules
1. **Licence:** contributions are accepted under the project licence (see `LICENSE`).
2. **Never commit secrets.** No keys, tokens, connection strings or customer data in code, tests, fixtures or issue text.
3. **Every feature ships with a test.** A capability that is not exercised by a test is not implemented, and must not be claimed in the README or the coverage scoreboard.
4. **Honest scope.** If something is a stub or prototype depth, the code and docs must say so (`# prototype depth:` comment).
5. **Schema changes go in `db/migrations/`,** never edited in place after being released.
6. **No feature gating.** Core modules are never moved behind a paid tier.

## Dev loop
```bash
cp .env.example .env
make up            # full stack
make status        # verify seeded data
make api-test      # tests
```

## Commit style
`area: imperative summary` e.g. `incident: add follow-up auto-close engine`, `db: add notification send log`.
