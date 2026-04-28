# Runbook: API key validation is slow

**Alert:** "WoT api: p95 latency above 2s" with most slow requests
on `/api/v1/*` endpoints that require an API key.
**Severity:** High.

API-key validation is on every request to a scope-gated endpoint.
When it is slow, every authenticated request is slow. Common culprits:
bcrypt CPU starvation, the prefix index missing, or N+1 queries on
the org join.

## 1. Triage (under 5 minutes)

```bash
PROJECT=aixcelerator-prod
SERVICE=wot-api
REGION=us-central1
```

```bash
# 1a. Confirm the slow path is auth-related, not the database.
# Healthz hits the DB but skips auth. If healthz is fast and authed
# endpoints are slow, the bottleneck is in validate_key.
curl -sS -w 'healthz: %{time_total}s\n' -o /dev/null \
    https://wot.aixcelerator.ai/api/v1/healthz

# Replace WOT_API_KEY with a known-good test key first:
curl -sS -w 'authed: %{time_total}s\n' -o /dev/null \
    -H "Authorization: Bearer $WOT_API_KEY" \
    https://wot.aixcelerator.ai/api/v1/systems/naics_2022
```

If `authed` is much slower than `healthz`, validation is the
bottleneck. If both are slow, see the cold-start runbook instead.

```bash
# 1b. p95 split by endpoint.
gcloud logging read \
    --project="$PROJECT" \
    "resource.labels.service_name=$SERVICE
     AND httpRequest.latency >= '2s'" \
    --limit=100 --order=desc \
    --format='value(httpRequest.requestUrl,httpRequest.latency)' \
    | head -20
```

## 2. Common causes (ranked)

### 2a. The api_key prefix index is missing or invalid

Most likely after a database restore, a manual table drop+recreate,
or a migration that did not finish. Validation falls back to a full
table scan.

```bash
gcloud sql connect wot-prod --project="$PROJECT" --user=postgres \
    --database=worldoftaxanomy <<'EOF'
\d api_key
-- Expect:
--   "idx_apikey_prefix" btree (key_prefix) WHERE revoked_at IS NULL
EOF
```

If the index is missing or invalid:

```sql
DROP INDEX IF EXISTS idx_apikey_prefix;
CREATE INDEX idx_apikey_prefix
    ON api_key(key_prefix) WHERE revoked_at IS NULL;
ANALYZE api_key;
```

### 2b. bcrypt cost is starving the CPU

`validate_key` runs bcrypt-checkpw on every request. If the cost factor
is too high (default is 12, ~250ms per check on Cloud Run small
instance), authenticated request rate is capped at ~4/s/instance.

```bash
gcloud sql connect wot-prod --project="$PROJECT" --user=postgres \
    --database=worldoftaxanomy <<'EOF'
SELECT substring(key_hash from 1 for 7) AS bcrypt_prefix, count(*)
FROM api_key WHERE revoked_at IS NULL
GROUP BY 1 ORDER BY 1;
EOF
-- Expect: $2b$12 (cost 12). Anything > 12 is too high.
```

Mitigation: scale Cloud Run horizontally (--max-instances higher).
Long term: lower the cost factor for newly issued keys; old keys
keep working at the existing cost.

### 2c. The org join is making validate_key do a sequential scan

Validation joins `api_key` -> `app_user` -> `org` to surface
`org_tier` + `rate_limit_pool_per_minute`. If app_user does not have
a primary-key index (it does, by default) or org's primary key is
missing, you'll see this.

```bash
gcloud sql connect wot-prod --project="$PROJECT" --user=postgres \
    --database=worldoftaxanomy <<'EOF'
EXPLAIN ANALYZE
SELECT k.id, u.org_id, o.tier
FROM api_key k
JOIN app_user u ON k.user_id = u.id
LEFT JOIN org o ON u.org_id = o.id
WHERE k.key_prefix = 'abcd1234'
  AND k.revoked_at IS NULL
LIMIT 5;
EOF
-- Expect Index Scans on api_key, app_user, and org.
-- A Seq Scan on any of these is the bug.
```

Fix: re-create the missing index. Migration 003 set
`idx_apikey_prefix` and `idx_app_user_org`; if either is gone,
re-run the relevant `CREATE INDEX` statement.

### 2d. Connection pool starvation

`validate_key` acquires a connection from the asyncpg pool; if the
pool is small and bcrypt takes 200ms, you can stack up.

Symptoms: requests stuck in "queueing for connection" state without
DB CPU or query latency rising.

```bash
gcloud sql connect wot-prod --project="$PROJECT" --user=postgres <<'EOF'
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
EOF
```

Tune the pool: increase `max-instances` on Cloud Run (more pool
copies) before increasing pool size per instance, since Cloud SQL
has its own `max_connections` ceiling.

## 3. Mitigation

While you investigate:

- Increase Cloud Run `--max-instances` to scale through the
  bcrypt CPU bottleneck:
  ```bash
  gcloud run services update wot-api \
      --project="$PROJECT" --region="$REGION" \
      --max-instances=20
  ```
- If a single key is hammering the service (org-throttle should
  prevent this, but verify), find the offending org_id in the
  access log and contact them or temporarily revoke the key.

## 4. Root cause

Capture EXPLAIN ANALYZE output for the validate_key query plan in
the post-incident note. If the plan shows Index Scan on every join
but is still slow, the bottleneck is bcrypt CPU; lower the cost on
new key issuance.

## 5. Followups

- Add a Prometheus histogram for `wot_validate_key_seconds` so this
  becomes graphable instead of correlating across logs.
- Consider a per-process LRU cache: cache `(key_prefix, key_hash)
  -> {user_id, org_id, scopes, org_tier}` for 60 seconds. Revoked
  keys clear from cache on the next validate cycle.
- If running on Cloud Run for a long time, the in-process cache
  matters even more during traffic spikes.
