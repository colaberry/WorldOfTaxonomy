# Runbook: Cloud Run cold start / latency spike

**Alerts:** "WoT api: p95 latency above 2s" or "WoT api: revision
restart loop".
**Severity:** High when latency is the symptom; Critical when the
service is in a restart loop and serving 5xx.

Cloud Run cold starts hit when the service scales from zero or when
a new revision rolls out. Symptoms include p95 latency spikes
without a corresponding rise in DB CPU. A revision restart loop is
when min-instances cannot stay up long enough to serve traffic.

## 1. Triage (under 5 minutes)

```bash
PROJECT=aixcelerator-prod
SERVICE=wot-api
REGION=us-central1
```

```bash
# 1a. Are we in a restart loop?
gcloud run services describe "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(status.latestReadyRevisionName,
                    status.conditions[0].status,
                    status.conditions[0].message)'
# Expect Ready=True. If False, follow the boot-failure path
# (see api-5xx.md, section 2d).
```

```bash
# 1b. How many instances right now? Are they fluctuating?
gcloud monitoring timeseries list \
    --project="$PROJECT" \
    --filter='metric.type = "run.googleapis.com/container/instance_count"
              AND resource.labels.service_name = "wot-api"' \
    --interval-end-time="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --interval-start-time="$(date -u -v-15M +%Y-%m-%dT%H:%M:%SZ)" \
    --format='value(points[0].value.int64Value)' | head -10
# A steady number = you have the right floor; a sawtooth = restart loop.
```

```bash
# 1c. Recent boot-time logs. Cold-start of a Python image typically
# takes 2-4 seconds; over 8 seconds means an import is slow.
gcloud logging read \
    --project="$PROJECT" \
    "resource.labels.service_name=$SERVICE
     AND textPayload:('Uvicorn running on' OR 'Application startup complete')" \
    --limit=10 --order=desc \
    --format='value(timestamp,textPayload)'
```

## 2. Common causes (ranked)

### 2a. Cold start because traffic dropped to zero

By default, Cloud Run scales to zero. The first request after an idle
period eats the cold-start cost (2-4s for a Python image with
asyncpg, more if Sentry initializes from cold). This shows up as
periodic p95 spikes that resolve automatically when warm.

Mitigation: set a minimum instance count.

```bash
gcloud run services update "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --min-instances=1
```

This pins one warm instance. Costs ~$10-15/mo for our image size at
us-central1 small. Worth it for any service that has paying users.

### 2b. New revision is starting up slowly

Roll-outs spawn a new revision. Old instances drain while new ones
boot; during that window, p95 spikes for fresh routes that hit the
new revision.

Confirm by listing the recent revisions and their birth times:

```bash
gcloud run revisions list \
    --service="$SERVICE" --project="$PROJECT" --region="$REGION" \
    --limit=5 \
    --format='table(metadata.name,metadata.creationTimestamp,status.conditions[0].status)'
```

If a revision is fresh (last few minutes) and the spike correlates,
this is normal rollout behavior. To shorten the window, set
`--max-instances` higher and `--min-instances >= 1` so the new
revision warms before traffic shifts.

### 2c. The boot path is doing too much

Bad import or a synchronous network call at module import time.
Common culprits in this codebase:

- Sentry initialization with a slow DSN handshake. Mitigation:
  unset `SENTRY_DSN` temporarily; verify cold-start drops; then
  re-test with the DSN.
- The wiki content build at import time (`build_llms_full_txt`).
  This is currently lazy (only called per /llms-full.txt request).
  Confirm it stays lazy on import.
- A blocking DB pool warm-up in lifespan that does a SELECT on a
  large table. The current `lifespan` only opens the pool; it does
  not pre-warm. If someone adds pre-warming, watch the cost.

```bash
# Time the import path locally:
time python3 -c 'from world_of_taxonomy.api.app import create_app; create_app()'
# Expect under 2s. Above 4s warrants an audit of recent changes.
```

### 2d. Concurrency setting is too low

Cloud Run defaults to 80 concurrent requests per instance. If we
set it lower, instance count balloons under load (each request
needs its own pod), making cold-starts more frequent.

```bash
gcloud run services describe "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(spec.template.spec.containerConcurrency)'
# Expect: 80 (default).
```

If lower, raise it back to 80 unless there's a documented reason.
Our handlers are I/O-bound (asyncpg), so 80 is the right default.

### 2e. Restart loop because a probe is failing

Cloud Run kills containers that fail their startup or liveness probe.
Check probe config:

```bash
gcloud run revisions describe \
    "$(gcloud run services describe "$SERVICE" \
        --project="$PROJECT" --region="$REGION" \
        --format='value(status.latestReadyRevisionName)')" \
    --project="$PROJECT" --region="$REGION" \
    --format='yaml(spec.containers[0].startupProbe,spec.containers[0].livenessProbe)'
```

The startup probe should hit `/api/v1/healthz`. If it hits a
non-existent path or has a tight timeout, the container will be
killed mid-boot. Forward-fix in the deploy spec.

## 3. Mitigation

In rough order:

1. Pin min-instances to 1 immediately. Stops the worst of the cold
   starts.
2. If restart loop: roll back to the previous revision (see
   `api-5xx.md` 2a).
3. If a new dependency is the slow import, pin to the previous
   image until you can investigate.

## 4. Root cause

Look at the boot-time log line "Uvicorn running on" (printed by
uvicorn) and measure delta from container creation timestamp to that
line. If delta > 4s, profile the import path.

## 5. Followups

- Set `--cpu-boost` on Cloud Run: gives the container 2x CPU during
  the first 10 seconds, which pays for itself on cold start.
  ```bash
  gcloud run services update "$SERVICE" \
      --project="$PROJECT" --region="$REGION" \
      --cpu-boost
  ```
- Add a Cloud Logging sink that emits a metric per cold start
  (filter on "Uvicorn running on") so we can graph cold-start
  frequency over time.
- If cold starts remain a problem, investigate switching to a
  lighter ASGI server (`hypercorn` or `granian`) and a slim base
  image.
