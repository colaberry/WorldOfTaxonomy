# Runbook: Running migrations

## Context

Schema changes land through [Alembic](https://alembic.sqlalchemy.org/). The tool is bootstrapped at the repo root (`alembic.ini`, `migrations/`). The baseline revision matches `world_of_taxonomy/schema.sql` + `schema_auth.sql` at the time of bootstrap; every subsequent change goes through a versioned migration.

## Local dev

```bash
# 1. Stamp an empty dev DB to the baseline so Alembic thinks we are caught up
export DATABASE_URL=postgres://localhost/wot_dev
alembic stamp head

# 2. Create a new migration after editing a model / writing raw SQL
alembic revision -m "add freshness_checked_at to classification_system"

# 3. Edit the generated file in migrations/versions/<rev>_...py
#    Fill in upgrade() with the change and downgrade() with the inverse.

# 4. Apply locally
alembic upgrade head

# 5. Smoke test
python3 -m pytest tests/ -q
```

## Production

Production migrations run as a one-shot command on a Fly machine **before** the new app version becomes healthy. The deploy pipeline does:

1. Build image.
2. Start a release-command container: `alembic upgrade head`.
3. If the migration succeeds, roll out new app machines.
4. If the migration fails, the deploy aborts; app traffic keeps hitting the old version.

Trigger a migration without shipping new app code:

```bash
fly deploy --strategy rolling --release-command "alembic upgrade head" -a wot-api
```

## Safe-change checklist

Every migration needs to be answered "yes" for each of these **before merging**:

- [ ] Is the change additive? (new column, new table, new index)
- [ ] If a column is new and the app writes to it: does the column have a default or is it nullable?
- [ ] If a column is dropped: has the app stopped reading it in a prior release?
- [ ] If the change is destructive (rename, type change, drop): is there a two-step plan (add new -> backfill -> switch reads -> drop old)?
- [ ] Has `alembic upgrade head` been tested against a copy of production data?
- [ ] Is there a `downgrade()` that works?

## Emergency: rolling a migration back

```bash
# Go back one revision
alembic downgrade -1

# Or go back to a specific revision
alembic downgrade <revision_id>
```

If the migration wrote data that the old schema cannot hold, `downgrade()` must handle the data too. See `deploy-rollback.md` for the broader rollback flow.

## Postmortem checklist

- Did the migration complete within the expected window?
- Did any long-running query block application traffic?
- Did the migration require a table rewrite (e.g. adding a column with a default on a large table)? If so, should it have been chunked?
- Is there a pattern worth documenting for the next similar change?
