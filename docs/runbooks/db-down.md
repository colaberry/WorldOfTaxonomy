# Runbook: Database down

## Symptom

- `/api/v1/healthz` returns `503` with `{"status": "degraded", "db": "fail"}`.
- API requests return 500 or time out.
- Log lines show `asyncpg.exceptions.ConnectionDoesNotExistError`, `CannotConnectNowError`, or repeated `TimeoutError` on `pool.acquire()`.

## Impact

- **All REST routes** except `/api/v1/healthz` and `/api/v1/version` fail.
- **MCP server** fails on any tool call that reads from Postgres (most of them).
- **Frontend** SSR pages fall back to their bundled `crosswalk-data/` snapshots where possible; live search, systems list, and user auth are dead.

## Detection

```bash
# Is the API reachable at all?
curl -s -o /dev/null -w "%{http_code}\n" https://wot.aixcelerator.app/api/v1/healthz

# Can we reach the database directly from the backend host?
fly ssh console -a wot-api -C 'python3 -c "import os; import asyncio; import asyncpg; \
    asyncio.run(asyncpg.connect(os.environ[\"DATABASE_URL\"]))"'
```

## Diagnosis

| Check | Command | Tells you |
|-------|---------|-----------|
| DB provider status page | Neon: <https://neon.tech/status>; Supabase: <https://status.supabase.com>; AWS: <https://health.aws.amazon.com/health/status> | Platform-wide outage |
| Fly app health | `fly status -a wot-api` | Backend container running? |
| Pool saturation | `grep "pool exhausted" /var/log/*.log` or Fly logs | Too many concurrent requests |
| DNS | `dig $DATABASE_HOST` | Database endpoint DNS resolving |
| DB compute state | Provider console (Neon branch, RDS instance, Supabase project) | Compute endpoint suspended or paused (cold start expected on serverless tiers) |

## Mitigation

1. **Restart the backend** to drop any stale pool state:
   ```bash
   fly apps restart wot-api
   ```
2. **Roll back** if the incident started after a deploy -- see `deploy-rollback.md`.
3. **Scale up** Fly machines if the issue is concurrency-bound:
   ```bash
   fly scale count 3 -a wot-api
   ```

## Remediation

- **If the DB provider is degraded**: nothing to do but wait for the provider to recover. Post a status update.
- **If DATABASE_URL has rotated**: update the Fly secret and restart:
  ```bash
  fly secrets set DATABASE_URL="postgres://..." -a wot-api
  ```
- **If the pool is configured too small**: bump `DB_POOL_MAX` (defaults to 20 in `world_of_taxonomy/db.py`) and redeploy.
- **If asyncpg cache is the issue** (prepared-statement errors on pgbouncer): confirm `statement_cache_size=0` still passed in `get_pool()`.

## Postmortem checklist

- Duration (first 503 -> first 200 on `/healthz`).
- User impact estimate (requests dropped / unique IPs affected).
- Upstream status (DB provider, Fly, Vercel) at the time.
- Whether alerts fired and how fast.
- Follow-ups: is `command_timeout` appropriate? Should retries be added at the query layer?
