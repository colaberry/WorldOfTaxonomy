# PostgreSQL major version upgrade — Cloud SQL `wot-db`

Runbook for upgrading the production `wot-db` instance from one major
PostgreSQL version to another (e.g. 15 → 17). Cloud SQL supports
**in-place major upgrades** that skip up to two majors per operation, so
15 → 17 is a single op.

This is a destructive-by-omission operation: the upgrade itself is
recoverable only by restoring a pre-upgrade backup to a NEW instance and
repointing services. Treat it like a database migration — written
ahead, communicated, executed in a maintenance window.

## When to upgrade

Upgrade when one of these is true:

- The current major is within 12 months of end-of-life
- A version-asymmetry friction we've felt repeatedly (e.g. team running
  `pg_dump <newer>` locally, can't restore into prod)
- A specific feature in a newer major matters for the workload
  (e.g. PG 17's MERGE-into-views, better JSON aggregates, faster VACUUM)

**Do not upgrade reactively** in response to a failed restore. Plan
properly and run in a maintenance window.

## Decision: which version to skip to

Cloud SQL supports skipping up to two majors. From PG 15 you can go to
17 in one op, but not 18+ in one op (need an intermediate hop).

If the team is already on a newer pg_dump locally, target THAT version
in prod so dumps roundtrip cleanly. Past that, target the latest
supported major in Cloud SQL (check
https://cloud.google.com/sql/docs/postgres/db-versions for current
support matrix).

## Pre-flight (T-48h)

### 1. Audit application + extension compatibility

```bash
# 1a. Confirm asyncpg / SQLAlchemy versions support the target major
grep -E "^(asyncpg|sqlalchemy|psycopg)" requirements.txt frontend/package.json

# 1b. Inspect installed extensions on the instance
gcloud sql databases list --instance=wot-db --project=colaberry-wot
# Connect via Cloud SQL Auth Proxy or a one-shot Cloud Run Job and:
#   SELECT * FROM pg_extension;
# Verify each is supported on the target major:
#   https://cloud.google.com/sql/docs/postgres/extensions
```

**Common breakages on major upgrades:**

- Removed views over `pg_proc.proisagg` (gone since PG 11)
- Removed ` ::regproc::oid` casts
- `pg_stat_statements` schema may need re-creating
- `tablefunc`, `pgcrypto`, `uuid-ossp` are stable across versions, no action

### 2. Validate backup chain

```bash
# Make sure backups are enabled and on a fresh schedule
gcloud sql instances describe wot-db --project=colaberry-wot \
  --format="value(settings.backupConfiguration)"

# Confirm we have a recent automated backup
gcloud sql backups list --instance=wot-db --project=colaberry-wot \
  --limit=3 --format="table(id,status,startTime,description)"
```

### 3. Run Cloud SQL's pre-check

Cloud SQL exposes a dry-run path for major upgrades that surfaces
incompatibility errors before you commit. Use it.

```bash
gcloud sql instances patch wot-db --project=colaberry-wot \
  --database-version=POSTGRES_17 \
  --quiet --async --dry-run 2>&1 | tee /tmp/pg17-precheck.log
```

If anything in the precheck output is `ERROR` or `WARN` (extension
incompatible, broken view, etc.), STOP and fix in a follow-up before
scheduling the window.

### 4. Schedule the maintenance window

- **Pick the lowest-traffic 60-minute slot for both team time-zones.**
  For Colaberry: 03:00–04:00 IST (= 17:30–18:30 PT prev day) typically
  works — India team asleep, US team end-of-day.
- 60 min covers worst case (15-30 min Cloud SQL upgrade + 15 min
  smoke-test + 15 min buffer for rollback if needed).
- Avoid the day before product demos, board meetings, or known-large
  user activity.

### 5. Communicate (T-48h)

- Post on Basecamp: maintenance-window note with start time, expected
  downtime, and the rollback contact.
- Email Ram + Karun + any external stakeholders consuming the API.
- If the public site has stakeholders watching status, post a status-page
  banner ahead of time — not just during.

## Pre-flight (T-2h)

### 6. Disable any triggers / cron that could collide

```bash
# Disable Cloud Build trigger so a stray push to main does not deploy
# during the upgrade
gcloud builds triggers update wot-main-autodeploy \
  --project=colaberry-wot --region=us-east1 --disabled
```

If you have ingest jobs or cron-fired Cloud Run Jobs, suspend them too.

### 7. Take a fresh on-demand backup

```bash
gcloud sql backups create --instance=wot-db --project=colaberry-wot \
  --description="Pre-upgrade-PG17-$(date -u +%Y%m%dT%H%M%SZ)"
```

Wait for it to reach `SUCCESSFUL` before continuing. This is the
canonical recovery point if the upgrade goes sideways.

```bash
gcloud sql backups list --instance=wot-db --project=colaberry-wot \
  --limit=1 --format="value(id,status,startTime,description)"
```

### 8. Confirm authorised contacts are online

Ram + Karun + on-call. Don't start the op if no one else is reachable.

## Execute (T-0)

### 9. Trigger the in-place upgrade

```bash
# Requested major version goes in --database-version
gcloud sql instances patch wot-db --project=colaberry-wot \
  --database-version=POSTGRES_17 \
  --quiet
```

The command returns once the patch operation is queued. The actual
upgrade runs asynchronously on Cloud SQL's side.

### 10. Watch the operation

```bash
# Tail the operation in a loop (until it completes)
until OP=$(gcloud sql operations list --instance=wot-db \
  --project=colaberry-wot --limit=1 \
  --format='value(operationType,status)' 2>&1); \
  echo "$OP" | grep -qE 'DONE|ERROR'; do echo "$OP"; sleep 30; done; echo "$OP"
```

**Expected timing for our 700 MB DB:**

- Stop accepting new connections: 30 sec
- Pre-upgrade snapshot: 1-2 min
- pg_upgrade in-place (link mode): 3-8 min
- Post-upgrade analyze + start: 2-5 min
- **Total: 10-20 min** for our size on `db-f1-micro`

Larger instances scale roughly with data volume.

### 11. Smoke test immediately after `DONE`

```bash
# Confirm reported version
gcloud sql instances describe wot-db --project=colaberry-wot \
  --format="value(databaseVersion)"
# expect: POSTGRES_17

# Hit the public API for known-good codes
for SAMPLE in "anzsic_2006:A:1000" "soc_2018:11-1011:300" "mesh:D007328:600" "icd_11:1A00:500"; do
  SYS="${SAMPLE%%:*}"
  REST="${SAMPLE#*:}"
  CODE="${REST%%:*}"
  MIN_LEN="${REST##*:}"
  URL="https://wot.aixcelerator.ai/api/v1/systems/$SYS/nodes/$CODE"
  DESC_LEN=$(curl -sf "$URL" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('description') or ''))")
  echo "  $SYS/$CODE description=$DESC_LEN chars"
  [ "$DESC_LEN" -ge "$MIN_LEN" ] || echo "    WARN: shorter than expected $MIN_LEN"
done

# MCP smoke
curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  https://wot.aixcelerator.ai/mcp \
  | python3 -c "import json,sys; r=json.load(sys.stdin); print(len(r.get('result',{}).get('tools',[])),'tools')"

# Frontend
curl -sfo /dev/null -w "frontend: %{http_code}\n" \
  https://www.worldoftaxonomy.com/
```

All four sample codes should return non-NULL descriptions of the
expected length. The MCP endpoint should return 26 tools. The
frontend should return 200.

### 12. Re-enable Cloud Build trigger

```bash
gcloud builds triggers update wot-main-autodeploy \
  --project=colaberry-wot --region=us-east1 --no-disabled
```

Verify the next push to main fires a build.

## Post-upgrade (T+24h)

### 13. Monitor

- Cloud SQL → wot-db → Observability → CPU / connections / IOPS /
  query latency. Watch for regressions vs the 24h before the upgrade.
- Cloud Run → wot-api / wot-web → Observability → error rate, p95
  latency, container restart counts.
- Application logs: `gcloud logging read` for `severity>=ERROR` on
  wot-api in the 1h after the upgrade. Anything new gets investigated
  before the upgrade is declared "done".

### 14. Update docs

- Bump the version mentioned in `README.md`, `HANDOVER.md`,
  `docs/architecture.md`.
- If `requirements.txt` pins `asyncpg`, double-check the pin is still
  valid for the new major. Bump if needed.

### 15. Tell the team it's done

Reply on the original maintenance-window thread with:
- Actual downtime (5-30 min usually)
- Final version
- Any anomalies observed
- Link to monitoring dashboards

## Rollback

In-place major upgrades are **not in-place reversible**. If the upgrade
itself fails or post-upgrade smoke tests fail unrecoverably:

```bash
# 1. Restore the pre-upgrade backup INTO A NEW INSTANCE (cannot
#    restore into the same instance after a major upgrade; it would
#    require a downgrade which Cloud SQL does not support).
gcloud sql instances clone wot-db wot-db-pg15-rollback \
  --project=colaberry-wot \
  --backup-id=<BACKUP_ID_FROM_STEP_7>

# 2. Repoint Cloud Run services to the new instance:
gcloud run services update wot-api \
  --project=colaberry-wot --region=us-east1 \
  --remove-cloudsql-instances=colaberry-wot:us-east1:wot-db \
  --add-cloudsql-instances=colaberry-wot:us-east1:wot-db-pg15-rollback

# 3. Update the DATABASE_URL secret to point at the new instance's
#    connection string (host=/cloudsql/colaberry-wot:us-east1:wot-db-pg15-rollback)
gcloud secrets versions add DATABASE_URL --data-file=- <<EOF
postgresql://wot:<password>@/worldoftaxonomy?host=/cloudsql/colaberry-wot:us-east1:wot-db-pg15-rollback
EOF

# 4. Bounce the wot-api revision to pick up the new socket
gcloud run services update wot-api --project=colaberry-wot \
  --region=us-east1 --update-env-vars=ROLLBACK_TIMESTAMP=$(date -u +%s)
```

Decommission the failed-upgrade instance once the rollback is verified
stable for 24h.

## Common failure modes + recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `pg_upgrade` fails at "checking for incompatible polymorphic functions" | Custom user-defined functions using removed `proisagg` | Drop the offending functions, re-run upgrade. Re-create from migrations after. |
| `wot-api` returns 5xx after upgrade | asyncpg / SQLAlchemy version doesn't recognise new on-the-wire types | Pin to the latest patch release of the driver, redeploy wot-api. |
| Connection-pool exhaustion immediately after upgrade | wot-api pool size + Cloud Run max-instances > Cloud SQL connection limit on new tier | Lower `max-instances` on wot-api temporarily, upgrade Cloud SQL tier next sprint. |
| Specific tables show row-count drift after the upgrade | Highly unlikely; would indicate corruption | Stop traffic, restore the pre-upgrade backup to a new instance, point services at it. |

## Reference

- Cloud SQL major upgrade docs:
  https://cloud.google.com/sql/docs/postgres/upgrade-major-db-version
- PostgreSQL 17 release notes:
  https://www.postgresql.org/docs/17/release-17.html
- Latest Cloud SQL version support matrix:
  https://cloud.google.com/sql/docs/postgres/db-versions
