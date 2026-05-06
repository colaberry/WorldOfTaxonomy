# Stripe end-to-end smoke test (test mode)

The 8-step verification you run after the Day 2 backend + Day 3 frontend
ship to staging, before flipping Stripe to live mode for public launch.

Prerequisites:
- Day 2 PR (#187) merged to main and deployed to staging
- Day 3 PR (frontend + cron) merged and deployed
- Stripe is in **test mode** (the default; verify the toggle in the
  Stripe dashboard top-right)
- Cloud Run Job `wot-stripe-overage` exists (per
  [stripe-overage-cron.md](stripe-overage-cron.md))
- A test email inbox you control (Mailtrap, Gmail, anything)

Time required: ~20 minutes.

## Test cards (use these instead of a real card)

| Number | Behavior |
|---|---|
| `4242 4242 4242 4242` | Always succeeds. Use for happy-path. |
| `4000 0000 0000 0341` | Trial succeeds; first invoice charge is declined. Use for dunning path. |
| `4000 0027 6000 3184` | Triggers 3D Secure (Strong Customer Authentication) flow. |

For all test cards: any future expiry, any 3-digit CVC, any postal code.

## The 8 steps

### 1. Sign up a fresh test account

- Open `https://staging.worldoftaxonomy.com/login` (or wherever staging lives)
- Enter a test email, click the magic link in your inbox
- Land on `/developers/keys`. Verify the **Billing panel** shows
  `tier = free` and an "Upgrade to Pro" button.

### 2. Click "Subscribe Monthly"

- Click "Upgrade to Pro" -> redirects to `/pricing`
- Click "Subscribe monthly" (toggle to monthly first if needed)
- Browser redirects to `checkout.stripe.com/c/pay/...`
- Use card `4242 4242 4242 4242`, any expiry/CVC/zip
- Stripe shows "Start trial" (14 days free)
- Click "Start trial"
- Stripe redirects to `staging.worldoftaxonomy.com/developers/keys?upgraded=true`

### 3. Verify the webhook fired and tier flipped

Within ~10 seconds of step 2:

- Reload `/developers/keys`. Billing panel should now show
  `tier = pro`, "Renews: <date>", and a "Manage subscription" button.

If the panel still shows `free`:
```bash
# Check Cloud Run logs for the wot-api service
gcloud run services logs tail wot-api --region=us-east1 \
  --filter='resource.labels.service_name=wot-api' \
  | grep -i "billing\|stripe"
```

Look for `customer.subscription.created` and a SQL UPDATE on the org row.
If the webhook never arrived, check the Stripe dashboard:
**Workbench -> Webhooks -> click the destination -> "Recent attempts"**.

### 4. Hit the Pro rate limit

Verify Pro = 5K req/min works (this is the Pro vs Free differentiator).

```bash
# Get the test user's API key from /developers/keys ("Generate key")
KEY=wot_xxxxx

# Quick smoke - hit /api/v1/search 100 times in 5 seconds
for i in $(seq 1 100); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $KEY" \
    "https://staging.worldoftaxonomy.com/api/v1/search?q=hospital"
done | sort | uniq -c
```

Expected: all 100 return `200`. Free tier (200/min) would 429 some.

### 5. Hit /classify above the included bucket

- Generate ~250 classify calls in a single day:

```bash
for i in $(seq 1 250); do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer $KEY" \
    -H "Content-Type: application/json" \
    -X POST -d '{"text": "trucking and freight transport"}' \
    "https://staging.worldoftaxonomy.com/api/v1/classify"
done | sort | uniq -c
```

Expected: all 250 return `200` (Pro has no hard cap).

Verify the counter:
```bash
gcloud sql connect wot-db --database=worldoftaxonomy --user=postgres -e "
  SELECT u.org_id, u.usage_date, u.count
  FROM org_classify_usage u JOIN org o ON o.id = u.org_id
  WHERE o.stripe_customer_id IS NOT NULL ORDER BY u.usage_date DESC LIMIT 5
"
```

Should show count = 250 (or close to it) for today.

### 6. Force the daily overage push

Skip waiting for the 03:00 UTC cron; trigger the job manually:

```bash
gcloud scheduler jobs run wot-stripe-overage-daily --location=us-east1
```

The job will see today's row but will only push if it's running for
"yesterday." For a same-day smoke test, run with an explicit date arg:

```bash
gcloud run jobs execute wot-stripe-overage \
  --region=us-east1 \
  --args=scripts/push_classify_overage.py,--date,$(date -u +%Y-%m-%d) \
  --wait
```

Expected log line:
```
INFO pushed 50 units for org=<uuid> customer=cus_xxxxx id=classify-overage-<uuid>-2026-MM-DD
```

Verify in Stripe dashboard:
**Workbench -> Events -> filter `billing.meter_event.created`** ->
should show the event with value=50, customer=cus_xxxxx.

Or check the customer's upcoming invoice:
**Customers -> click the test customer -> Subscriptions -> click the active
sub -> "Upcoming invoice"** -> should show metered line item with 50 units.

### 7. Open the Customer Portal and cancel

- On `/developers/keys`, click "Manage subscription"
- Browser redirects to `billing.stripe.com/p/session/...`
- Click "Cancel subscription" -> "Cancel at period end" -> Confirm
- Click "Return to merchant" or close the tab
- Back on `/developers/keys`, the Billing panel should still show
  `tier = pro` (cancellation is graceful; takes effect at period end)

To force the immediate cancellation for testing, use the dashboard:
**Customers -> click test customer -> Subscriptions -> click sub -> "Cancel
subscription" -> "Cancel immediately"**.

Then within ~10 seconds the webhook fires `customer.subscription.deleted`
and tier flips back to `free`. Reload `/developers/keys` to verify.

### 8. Test the dunning path (declined card)

Repeat steps 1-2 with a fresh test email and card `4000 0000 0000 0341`:
- Trial starts successfully (Stripe doesn't charge during trial)
- After 14 trial days end, Stripe attempts the first $49 charge -> declined
- `invoice.payment_failed` webhook fires -> we log + send Resend email
  (TODO post-launch; for now just verify the log line exists)
- Stripe retries dunning for ~3 weeks; user keeps `tier = pro` during this
- After Stripe gives up: `customer.subscription.deleted` fires -> tier = `free`

Skip-the-wait shortcut for testing: in the Stripe dashboard,
**Customers -> test customer -> Subscriptions -> click sub -> "Actions" ->
"Cancel subscription"** simulates the end-of-dunning event.

## Pass/fail criteria

All 8 steps must pass for the smoke test to be green. If any step fails:

1. Check Cloud Run logs: `gcloud run services logs tail wot-api`
2. Check the Stripe dashboard's Webhook destination for failed deliveries
3. Check the DB: `SELECT * FROM processed_stripe_events ORDER BY processed_at DESC LIMIT 10`
4. If the `processed_stripe_events` table has rows but the org tier
   didn't change, the dispatch table is wrong -> debug the matching handler

## After all 8 steps pass

You're cleared to flip Stripe from test mode to live mode. The flip is
a single toggle in the Stripe dashboard, but it requires:

- Business onboarding complete (legal entity, bank account, tax info)
- Live-mode Price IDs (Stripe creates these separately from test mode)
- Live-mode webhook endpoint configured
- Live-mode `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and the three
  `STRIPE_PRICE_ID_*` vars rotated in GCP Secret Manager
- One smoke iteration in live mode against your own real card before
  announcing publicly

That's the bridge from test mode to launch-ready.
