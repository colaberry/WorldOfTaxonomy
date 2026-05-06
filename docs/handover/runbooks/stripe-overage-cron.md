# Daily Stripe overage cron

The script `scripts/push_classify_overage.py` runs once per day to
push yesterday's per-org `/classify` overage to Stripe as Meter Events.
Stripe rolls those into the next monthly invoice at $0.05 per unit.

This runbook covers the one-time GCP setup (Cloud Run Job + Cloud
Scheduler trigger) and the steady-state operations (debug, replay,
backfill).

## What the script does

1. Connect to Cloud SQL via `DATABASE_URL`.
2. `SELECT org_id, count, stripe_customer_id FROM org_classify_usage
    JOIN org WHERE usage_date = yesterday AND count > 200 AND tier IN
    ('pro', 'enterprise') AND stripe_customer_id IS NOT NULL`.
3. For each row, call `stripe.billing.MeterEvent.create(event_name=
   'wot_classify_call', payload={stripe_customer_id, value: count - 200},
   identifier='classify-overage-{org_id}-{date}')`.
4. Stripe dedupes by `identifier` within a 24h window; re-running for
   the same day is a no-op.

The `--date YYYY-MM-DD` flag lets you replay a specific day. Default
is yesterday UTC.

## One-time setup (Cloud Run Job + Scheduler)

Run from your dev shell once. All commands assume `gcloud config set
project colaberry-wot` is set.

### 1. Create the Cloud Run Job

```bash
IMAGE="us-east1-docker.pkg.dev/colaberry-wot/wot-repo/wot-api:latest"
INSTANCE_CONN="colaberry-wot:us-east1:wot-db"

gcloud run jobs create wot-stripe-overage \
  --image="$IMAGE" \
  --region=us-east1 \
  --set-cloudsql-instances="$INSTANCE_CONN" \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest \
  --command=python \
  --args=scripts/push_classify_overage.py \
  --task-timeout=600 \
  --max-retries=1
```

The job pulls the same image as `wot-api` so it has the same Python
deps and the same `world_of_taxonomy` package on the path.

### 2. Create the Cloud Scheduler trigger

```bash
SCHEDULER_SA="$(gcloud projects describe colaberry-wot \
  --format='value(projectNumber)')-compute@developer.gserviceaccount.com"

gcloud scheduler jobs create http wot-stripe-overage-daily \
  --location=us-east1 \
  --schedule="0 3 * * *" \
  --time-zone="UTC" \
  --uri="https://us-east1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/colaberry-wot/jobs/wot-stripe-overage:run" \
  --http-method=POST \
  --oauth-service-account-email="$SCHEDULER_SA" \
  --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
  --description="Push prior-day /classify overage to Stripe Meter Events"
```

Schedule explanation: `0 3 * * *` = 03:00 UTC daily. The job runs after
midnight UTC so "yesterday" in the script means yesterday's complete
day in UTC. Adjust if you switch to a different timezone for billing.

### 3. Grant Scheduler permission to invoke the Job

```bash
gcloud run jobs add-iam-policy-binding wot-stripe-overage \
  --region=us-east1 \
  --member="serviceAccount:${SCHEDULER_SA}" \
  --role="roles/run.invoker"
```

### 4. Smoke-test the trigger

Force an immediate run:

```bash
gcloud scheduler jobs run wot-stripe-overage-daily --location=us-east1
```

Watch the logs:

```bash
gcloud run jobs executions list \
  --job=wot-stripe-overage \
  --region=us-east1 \
  --limit=5

# Most recent execution's logs:
gcloud run jobs executions logs tail \
  --execution=$(gcloud run jobs executions list \
    --job=wot-stripe-overage --region=us-east1 \
    --limit=1 --format='value(name)')
```

Expected output:
```
INFO pushing classify overage for day=YYYY-MM-DD included_bucket=200
INFO no orgs with overage for YYYY-MM-DD; nothing to push
INFO done: orgs_seen=0 orgs_pushed=0 units_pushed=0
```

That "nothing to push" line is the healthy steady-state until you have
Pro customers exceeding 200 calls/day.

## Day-to-day operations

### Replaying a specific day

If a day's run failed (e.g., DATABASE_URL was rotated and the secret
hadn't been re-bound yet), replay manually:

```bash
gcloud run jobs execute wot-stripe-overage \
  --region=us-east1 \
  --args=scripts/push_classify_overage.py,--date,2026-05-04 \
  --wait
```

The script's stable `identifier` means re-running is safe; Stripe
dedups within 24h. After 24h, a re-run could create a duplicate
charge, so DO NOT replay a day older than 24h without first checking
the Stripe dashboard for existing meter events with the same
`identifier`.

### Inspecting what was pushed

In the Stripe dashboard (test or live mode):

1. **Workbench -> Events** -> filter by `billing.meter_event.created`
2. **Subscriptions** -> any Pro customer -> "Upcoming invoice" -> see the
   metered line item with the running total

### Reconciling DB with Stripe

Use this query to compare `org_classify_usage` totals with what we
should have pushed:

```sql
SELECT
  o.id AS org_id,
  o.stripe_customer_id,
  u.usage_date,
  u.count AS used_today,
  GREATEST(u.count - 200, 0) AS expected_overage_units
FROM org_classify_usage u
JOIN org o ON o.id = u.org_id
WHERE o.tier = 'pro'
  AND u.usage_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY u.usage_date DESC, o.id;
```

Cross-check `expected_overage_units` against the meter event counts in
Stripe for the same day.

## Common failure modes

### "STRIPE_SECRET_KEY is not set"
The Cloud Run Job is missing the secret binding. Re-bind:
```bash
gcloud run jobs update wot-stripe-overage \
  --region=us-east1 \
  --update-secrets=STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest
```

### "No matching meter found" / 404 from Stripe
The `STRIPE_METER_EVENT_NAME` env var doesn't match the meter you
created in the dashboard. The script defaults to `wot_classify_call`;
if you renamed the meter, set the env var to match. Check:
```bash
gcloud secrets versions access latest --secret=STRIPE_METER_EVENT_NAME 2>/dev/null \
  || echo "(unset; default 'wot_classify_call')"
```

### Pushed wrong amount
If a day's count is off (e.g., bug in counter), the recovery is:
1. Stop the cron immediately: `gcloud scheduler jobs pause wot-stripe-overage-daily --location=us-east1`
2. Issue a credit note in Stripe for the affected customer (Stripe
   dashboard -> customer -> "Issue credit note")
3. Fix the bug, then resume: `gcloud scheduler jobs resume wot-stripe-overage-daily --location=us-east1`

Never delete meter events directly; Stripe doesn't support that. Always
fix forward via credit notes.

### Job runs but pushes 0 events when you expect overage
- Check `org_classify_usage` has rows for yesterday: `SELECT * FROM
  org_classify_usage WHERE usage_date = CURRENT_DATE - 1`
- Check the org has `tier = 'pro'` and `stripe_customer_id IS NOT NULL`
- Check the `count > 200` filter (overage only fires above the bucket)

## Followups

- [ ] Add `--dry-run` flag to the script for safer manual replays.
- [ ] Send a Sentry breadcrumb on each push so we can correlate with
      invoice anomalies later.
- [ ] After 6 months of data, evaluate switching to graduated overage
      tiers ($0.05/100 first, $0.02 next 1K, $0.01 above 1K). Today's
      flat rate is the v1 simplification.
