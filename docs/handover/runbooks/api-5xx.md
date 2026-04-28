# Runbook: API is 5xx-ing

**Alert:** "WoT api: 5xx rate above 1%" or generic 5xx user reports.
**Severity:** Critical (paging).

## 1. Triage (under 5 minutes)

Run these in order. The first one that returns a clear signal stops
the search.

```bash
PROJECT=aixcelerator-prod
SERVICE=wot-api
REGION=us-central1
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# 1a. Is the service serving anything?
curl -sS -i https://wot.aixcelerator.ai/api/v1/healthz | head -3
# Expect: HTTP/1.1 200 OK and {"status":"ok","db":"ok",...}
```

```bash
# 1b. What's the active revision and how many instances?
gcloud run services describe "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(status.latestReadyRevisionName,status.traffic[0].percent)'
gcloud run revisions describe \
    "$(gcloud run services describe "$SERVICE" \
        --project="$PROJECT" --region="$REGION" \
        --format='value(status.latestReadyRevisionName)')" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(status.conditions[0].status,status.observedGeneration)'
```

```bash
# 1c. Last 50 lines of Cloud Logging filtered to errors and 5xx.
gcloud logging read \
    --project="$PROJECT" \
    "resource.labels.service_name=$SERVICE
     AND (severity>=ERROR OR httpRequest.status>=500)" \
    --limit=50 --order=desc \
    --format='value(timestamp,httpRequest.status,httpRequest.requestUrl,jsonPayload.error,textPayload)' \
    | head -50
```

```bash
# 1d. Sentry inbox (if you can reach it from a browser):
#     https://sentry.io/organizations/.../issues/?query=is:unresolved+age:-1h&project=wot-api
# Look for a single dominant error_type in the last 30 minutes.
```

## 2. Common causes (ranked)

### 2a. Recent deploy is broken

Most likely cause when 5xx rate spikes within minutes of a deploy.

```bash
# Promote 100% of traffic back to the previous revision:
PREV=$(gcloud run revisions list \
    --service="$SERVICE" --project="$PROJECT" --region="$REGION" \
    --format='value(metadata.name)' \
    --filter='status.conditions.type=Ready AND status.conditions.status=True' \
    --limit=2 | sed -n '2p')

gcloud run services update-traffic "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --to-revisions="$PREV=100"
```

Then investigate what changed in the broken revision and forward-fix
in a follow-up PR.

### 2b. Database is unreachable or slow

Healthz reports `"db": "fail"` or returns 503. Check Cloud SQL:

```bash
gcloud sql instances describe wot-prod \
    --project="$PROJECT" \
    --format='value(state,settings.activationPolicy)'
# Expect: RUNNABLE, ALWAYS
```

If the instance is RUNNABLE, the connection from Cloud Run may be
exhausted. Check `pg_stat_activity` for max connections:

```bash
gcloud sql connect wot-prod --project="$PROJECT" --user=postgres <<'EOF'
SELECT count(*) FROM pg_stat_activity;
SELECT setting FROM pg_settings WHERE name = 'max_connections';
EOF
```

Mitigation: temporarily increase Cloud Run min-instances to keep
connections warm, OR temporarily increase Cloud SQL max_connections
in the instance settings (requires brief restart).

### 2c. A specific endpoint is throwing

Filter the log query by URL:

```bash
gcloud logging read \
    --project="$PROJECT" \
    "resource.labels.service_name=$SERVICE
     AND httpRequest.status>=500" \
    --limit=100 --order=desc \
    --format='value(httpRequest.requestUrl)' \
    | sort | uniq -c | sort -rn | head -10
```

If 80%+ of 5xx are on one path (say `/api/v1/classify`), that handler
is the culprit. Possible mitigations:

- Add a temporary feature flag to disable that endpoint while you fix.
- If it is a Pro+ paid endpoint, you can return a maintenance message
  with 503 + Retry-After.

### 2d. Container won't start (instance restart loop)

If `gcloud run revisions describe` shows `status.conditions[0].status=False`
or instance count is churning, the new revision is failing at boot.

```bash
gcloud logging read \
    --project="$PROJECT" \
    "resource.labels.service_name=$SERVICE
     AND textPayload:('Error' OR 'Traceback' OR 'EnvConfigError')" \
    --limit=20 --order=desc
```

Common boot-time failures:

- `EnvConfigError: DATABASE_URL is required` - missing secret binding.
- `EnvConfigError: JWT_SECRET must be at least 32 characters` -
  truncated env var.
- `asyncpg.exceptions.InvalidPasswordError` - rotated DB password
  not yet propagated to Cloud Run.

Forward-fix in deployment, NOT in code.

## 3. Mitigation

While you investigate, the bleeding stops by:

1. Rolling back to the last known-good revision (see 2a).
2. Hard-disabling the affected endpoint (return 503 + `Retry-After`
   in middleware temporarily).
3. Routing 100% of traffic to a previous revision via:
   ```bash
   gcloud run services update-traffic "$SERVICE" \
       --project="$PROJECT" --region="$REGION" \
       --to-revisions="$PREV_GOOD=100"
   ```

Do this BEFORE finishing your investigation. Stop the bleeding,
then debug.

## 4. Root cause

Once the rollback or temporary fix is in place:

- Pull the matching Sentry event (the alert documentation links to
  the docs runbook; the documentation field on the alert policy
  embeds this filename so the on-call can find it from the Cloud
  Monitoring detail page).
- Read the stack trace + the request_id correlation in Cloud Logging.
- Add a regression test that fails with the same shape, then fix.

## 5. Followups

After the incident is closed:

- Create a GitHub issue tagged `incident-followup` referencing the
  date and the request_id.
- If this is the second time the same alert has fired, escalate the
  fix priority - it is no longer a one-off.
- If the alert was noisy (fired but no action was needed), tune the
  threshold in `scripts/phase6_setup_alerts.sh` and re-run.
