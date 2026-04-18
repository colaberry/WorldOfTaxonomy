# Runbooks

Incident response playbooks for WorldOfTaxonomy. Each runbook is written to be picked up cold by someone on-call who has never seen the specific incident before.

## Structure of each runbook

- **Symptom**: what operators see first (alert, log line, user report).
- **Impact**: who is affected and how badly.
- **Detection**: where to verify the problem (URL, command, dashboard).
- **Diagnosis**: the minimum set of steps to confirm the cause.
- **Mitigation**: the first action to take to reduce impact.
- **Remediation**: the full fix.
- **Postmortem checklist**: what to capture before closing the ticket.

## Index

- [db-down.md](db-down.md) -- Postgres pool unreachable / `/healthz` returning 503
- [auth-broken.md](auth-broken.md) -- 401/403 spike, JWT verification failing, OAuth callbacks erroring
- [ingest-failed.md](ingest-failed.md) -- Monthly ingest-refresh workflow red; stale data warning
- [rate-limit-abuse.md](rate-limit-abuse.md) -- Legit users hitting 429 or a single IP/user saturating capacity
- [deploy-rollback.md](deploy-rollback.md) -- Backend or frontend deploy regressed; how to revert quickly
- [migrations.md](migrations.md) -- Running Alembic migrations in dev and production

## Conventions

- All commands assume you are in the repo root.
- Know your DB provider's point-in-time recovery (PITR) window and plan restores against it. Examples: Neon Free tier 30 days, RDS up to 35 days, Supabase varies by tier; self-hosted uses whatever your backup policy is.
- Backend logs are JSON (one request per line) in `stdout`. In prod they land in Fly's log stream.
- Sentry environment is set by `SENTRY_ENVIRONMENT` (default `development`). Production tag is `production`.

## When a runbook is missing

If you hit a new class of incident:

1. Stabilize first (rollback, disable the offending system, escalate).
2. Write the runbook **during** the postmortem, not after.
3. Link it from this index.
