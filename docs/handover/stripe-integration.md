# Stripe Integration Handover

> **Hi - if you're reading this, you've been asked to wire Stripe
> into WorldOfTaxonomy. This doc tells you what to build, in what
> order, with the locked pricing decisions baked in. ~3 days of
> work end to end. No PCI scope - we never touch card numbers.**
>
> Read time: 25 minutes.
> Owner: Ram Katamaraja, Colaberry AI.
> Last refresh: 2026-05-04.
> Pricing source of truth: `.claude/.../memory/project_pricing_tiers.md`
> (locked 2026-05-04 - do not freelance the numbers).

---

## 1. What you're building, in one paragraph

A self-serve subscription flow that takes a logged-in WoT user from
"I want Pro" to a working Pro tier in two clicks. Stripe-hosted
Checkout for the card capture, Stripe-hosted Customer Portal for
plan changes / cancellations, and a webhook handler that flips
`org.tier` based on subscription state. Plus metered overage on
`/classify` (Stripe usage-based billing) at $0.05/call above the
included bucket.

Three new endpoints (`/billing/checkout`, `/billing/portal`,
`/billing/webhook`), one schema migration, two frontend buttons,
two GCP secrets. That's it.

---

## 2. Locked pricing (do not freelance)

### Free ($0)
- 30/min anonymous, 200/min authenticated, 50K req/day cap
- 20 /classify calls/day
- MCP stdio mode only

### Pro ($49/month or $490/year)
- 5,000/min, unlimited daily
- 200 /classify calls/day **included**
- /classify overage **$0.05 per call** above the bucket
- MCP HTTP-mode (hosted)
- Bulk JSON export
- Webhook notifications on ingest refresh
- Per-key analytics dashboard
- 14-day free trial, card required
- Annual discount: $490/yr is ~17% off ($588 - $98)

### Enterprise ($499/month floor, sales-led)
- 50,000+/min, custom
- Unlimited /classify (or custom cap)
- 99.9% SLA, audit log export, private classification systems
- Annual contract, invoiced. **Do not put a price on the marketing page; show "Contact us".**

Full rationale and rejected alternatives in the memory entry. If you
think a number should change, talk to Ram before changing it.

---

## 3. Architecture

```
Browser                                 Stripe                          Backend
   |                                       |                               |
   |  click "Subscribe" on /pricing        |                               |
   +---------------------------------------|-> POST /billing/checkout ---->|
   |                                       |                               | create Checkout Session
   |  302 redirect to checkout.stripe.com  |<------------------------------+ for Pro Price ID
   |                                       |                               |
   |  user enters card                     |                               |
   |  Stripe charges, creates subscription |                               |
   |                                       |  POST /billing/webhook        |
   |  302 back to /developers/keys         |  customer.subscription.created
   |                                       +------------------------------>|
   |                                       |                               | UPDATE org SET tier='pro',
   |                                       |                               | stripe_subscription_id=...
   |                                       |                               |
   |  next API request                     |                               | rate limiter sees tier='pro'
   |---------------------------------------|------------------------------>| -> serves at 5K/min cap
```

For the Customer Portal (cancellation, plan change) the flow is the
same shape: backend creates a Portal Session, browser redirects to
Stripe, Stripe webhooks back the new state, backend flips `org.tier`.

For metered overage on `/classify`, the rate limiter increments a
local counter; once a day a small cron pushes the daily count to
Stripe via `SubscriptionItem.create_usage_record`, and Stripe rolls
it into the next monthly invoice.

---

## 4. What's already in place

| Piece | Status | Where |
|---|---|---|
| `org` table with `tier` enum (free/pro/enterprise) | ✅ exists | [schema_devkeys.sql:8-20](../../world_of_taxonomy/schema_devkeys.sql) |
| `org.stripe_customer_id TEXT UNIQUE` column | ✅ exists | same |
| `org.zitadel_org_id` (placeholder for future) | ✅ exists | same |
| Rate limiter reads `org_tier` from session | ✅ exists | [api/deps.py:108](../../world_of_taxonomy/api/deps.py) |
| Tier-aware rate cap in middleware | ✅ exists | [api/middleware.py](../../world_of_taxonomy/api/middleware.py) |
| Magic-link auth + `dev_session` cookie | ✅ exists | (Phase 6) |
| Frontend `/pricing` page (placeholder) | ✅ exists | [frontend/src/app/pricing/page.tsx](../../frontend/src/app/pricing/page.tsx) |
| `/developers/keys` dashboard | ✅ exists | (Phase 6) |

What's NOT in place:
- `stripe_subscription_id` and `tier_active_until` columns on `org`
- `classify_overage_count` daily counter (or use existing `daily_usage`)
- Stripe SDK in `requirements.txt`
- Three `/billing/*` endpoints
- Webhook event-handler dispatch
- Frontend "Subscribe" button + "Manage subscription" button
- Stripe account, Products, Prices, Webhook endpoint config

---

## 5. Day 1 - Stripe-side setup (no code)

You need a Stripe account and a couple of decisions made on the
Stripe dashboard before any code can land.

### 5.1. Provision the account

If Colaberry AI already has a Stripe org, ask Ram for access. Otherwise:

- Sign up at stripe.com using a Colaberry-controlled email.
- Set the legal business name and tax info during onboarding.
- Stripe will keep you in **test mode** until business onboarding is
  complete. You can build everything against test mode; flip to live
  mode for the final QA.

### 5.2. Create Products + Prices

In **Products**, create three:

#### Product 1: "World Of Taxonomy Pro"
- Description: "5K req/min, 200 classify/day included, MCP HTTP mode, bulk export, webhooks"
- Pricing model: Standard pricing
- Add three Prices under this Product:
  - **Pro Monthly**: $49.00 USD, billed monthly, recurring
  - **Pro Annual**: $490.00 USD, billed yearly, recurring
  - **Pro Overage** (metered): $0.05 USD per unit, recurring monthly,
    "Usage is metered" toggle ON, aggregation = "Sum of usage values
    during period." This is what bills the /classify overage.

#### Product 2: "World Of Taxonomy Enterprise"
- Skip creating Prices in Stripe. Enterprise is sales-led; you'll
  generate Price objects ad-hoc for each contract. The Product just
  exists so the dashboard is organized.

#### Product 3: (skip)
- "Free" doesn't need a Stripe Product. Free users have no Stripe
  Customer record until they upgrade.

**Capture the Price IDs** (look like `price_1QxYz...`). You'll wire
these into env vars on Day 3.

### 5.3. Configure the Customer Portal

Stripe Dashboard → **Settings** → **Billing** → **Customer Portal**:

- "Allow customers to update payment method": ON
- "Allow customers to update billing address": ON
- "Allow customers to cancel subscription": ON
- Cancellation: "At the end of the billing period" (graceful)
- "Allow customers to switch plans": ON, with both Pro Monthly + Pro Annual as switchable
- Invoice history: ON

Save. The Portal is now usable.

### 5.4. Configure the Webhook endpoint

Stripe Dashboard → **Developers** → **Webhooks** → "Add endpoint":

- URL: `https://wot.aixcelerator.ai/api/v1/billing/webhook`
- Events to listen for (minimum):
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
  - `customer.subscription.trial_will_end`

Save. Stripe shows you the signing secret (`whsec_...`); you'll need
it in Day 3.

### 5.5. Capture the secrets

You now have four secrets to put into GCP Secret Manager:
- `STRIPE_PUBLISHABLE_KEY` (`pk_test_...` for test, `pk_live_...` later)
- `STRIPE_SECRET_KEY` (`sk_test_...` / `sk_live_...`)
- `STRIPE_WEBHOOK_SECRET` (`whsec_...`)
- `STRIPE_PRICE_ID_PRO_MONTHLY`, `STRIPE_PRICE_ID_PRO_ANNUAL`,
  `STRIPE_PRICE_ID_PRO_OVERAGE` (these aren't secrets technically,
  but stash in env for clean rotation)

End of Day 1.

---

## 6. Day 2 - Database + backend

### 6.1. Schema migration

Add new Alembic revision. Skeleton:

```sql
-- migrations/versions/0004_stripe_subscription_state.py
ALTER TABLE org
    ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS tier_active_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS stripe_overage_meter_id TEXT;
    -- stripe_overage_meter_id is the SubscriptionItem ID of the
    -- metered Pro Overage line item, used by the daily usage push.

CREATE INDEX IF NOT EXISTS idx_org_stripe_subscription
    ON org(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
```

Run via the standard `alembic upgrade head` flow ([cicd-deployment.md](cicd-deployment.md)).

### 6.2. Add Stripe SDK

```
# requirements.txt
stripe==9.x  # latest stable as of writing
```

### 6.3. Endpoint contracts

Three new endpoints under a new router `world_of_taxonomy/api/routers/billing.py`:

#### POST /api/v1/billing/checkout
- Auth: cookie session required (`get_current_user`).
- Request body: `{"plan": "pro_monthly"}` or `{"plan": "pro_annual"}`.
- Behavior:
  1. Look up `current_user.org_id` -> get/create the Stripe Customer
     (if `org.stripe_customer_id` is null, create one and persist).
  2. Create a Checkout Session: mode=subscription, customer=that ID,
     line_items=[{price: PRICE_ID_PRO_MONTHLY_OR_ANNUAL, quantity: 1},
                 {price: PRICE_ID_PRO_OVERAGE}], # the metered line
     success_url=https://wot.aixcelerator.ai/developers/keys?upgraded=true,
     cancel_url=https://wot.aixcelerator.ai/pricing?canceled=true,
     subscription_data={"trial_period_days": 14, "metadata": {"org_id": org.id}}
  3. Return `{"checkout_url": session.url}` (302-equivalent for the JS to follow).
- Idempotency: if the org already has an active Pro subscription, return 409.

#### POST /api/v1/billing/portal
- Auth: cookie session required.
- Request body: `{}` (no payload).
- Behavior:
  1. If `org.stripe_customer_id` is null: 404 "no subscription".
  2. Create a billing Portal Session: customer=that ID,
     return_url=https://wot.aixcelerator.ai/developers/keys.
  3. Return `{"portal_url": session.url}`.

#### POST /api/v1/billing/webhook
- Auth: NONE (Stripe calls this directly). Use Stripe-Signature
  header validation instead - reject any request with a bad signature.
- Body: raw JSON (do not Pydantic-parse the whole event;
  `stripe.Webhook.construct_event` validates and parses).
- Behavior: dispatch table by event type:

```python
# world_of_taxonomy/api/routers/billing.py
EVENT_HANDLERS = {
    "customer.subscription.created":  _on_subscription_active,
    "customer.subscription.updated":  _on_subscription_active,
    "customer.subscription.deleted":  _on_subscription_canceled,
    "invoice.payment_succeeded":      _on_payment_succeeded,
    "invoice.payment_failed":         _on_payment_failed,
    "customer.subscription.trial_will_end": _on_trial_ending,
}
```

Each handler is **idempotent** - Stripe retries on 5xx, and you'll
get the same event multiple times. Use Stripe's `event.id` as a
dedup key (small `processed_stripe_events` table or Redis SET).

`_on_subscription_active`:
- Look up `org` by `metadata.org_id` (set in Checkout).
- `UPDATE org SET tier='pro', stripe_subscription_id=...,
   stripe_overage_meter_id=<the metered SubscriptionItem.id>,
   tier_active_until=<period_end>;`

`_on_subscription_canceled`:
- `UPDATE org SET tier='free', stripe_subscription_id=NULL;`
  (keep `stripe_customer_id` so they can resubscribe.)

`_on_payment_failed`:
- Don't downgrade immediately. Stripe retries dunning for 3 weeks.
- Email the org owner via Resend (template: "your payment failed").
- After Stripe gives up (event arrives as `subscription.deleted`),
  the cancel handler runs and downgrades.

`_on_payment_succeeded`:
- Extend `tier_active_until` to the new `current_period_end`.
- Reset any monthly counters that tier needs.

`_on_trial_ending`:
- Email the org owner: "trial ends in 3 days, your card will be charged."

### 6.4. Metered usage push (daily cron)

A small daily job that bumps Stripe with the day's overage count:

```python
# scripts/push_classify_overage.py (new file, runs as Cloud Run Job)
async def main():
    today = date.today() - timedelta(days=1)
    rows = await fetch("""
        SELECT org_id, classify_count
        FROM daily_usage
        WHERE day = $1 AND classify_count > 200
    """, today)
    for row in rows:
        overage = row["classify_count"] - 200
        org = await fetch_org(row["org_id"])
        if not org.stripe_overage_meter_id:
            continue  # not on Pro, no overage applies
        stripe.SubscriptionItem.create_usage_record(
            org.stripe_overage_meter_id,
            quantity=overage,
            timestamp=int(today.timestamp()),
            action="set",  # idempotent re-run
        )
```

Wire as a Cloud Run Job + Cloud Scheduler trigger (1× per day at
03:00 UTC). The `action="set"` makes the script idempotent if it
runs twice for the same day.

End of Day 2.

---

## 7. Day 3 - Frontend + secrets

### 7.1. Frontend changes

**`/pricing` page** ([frontend/src/app/pricing/page.tsx](../../frontend/src/app/pricing/page.tsx)):

- Render three cards: Free, Pro, Enterprise.
- Pro card has TWO buttons: "Subscribe Monthly $49/mo" and
  "Subscribe Annually $490/yr (save 17%)".
- Each Subscribe button POSTs to `/api/v1/billing/checkout` with
  the plan key, then `window.location = response.checkout_url`.
- Enterprise card says "Contact us", links to `/contact`.
- Free card says "Get started", links to `/login` (or
  `/developers/keys` if already signed in).

**`/developers/keys` dashboard**:

- Add a "Billing" panel:
  - If `org.tier === 'free'`: show "Upgrade to Pro" button → /pricing.
  - If `org.tier === 'pro'`: show "Manage subscription" button →
    POSTs to `/api/v1/billing/portal`, redirects to Stripe Portal.
  - Show current period (read from `tier_active_until`).
  - Show classify usage today vs. 200/day cap, with a hint
    "overage at $0.05/call applies above 200/day."

**Loading state on Subscribe button**: show a spinner; the round
trip to Stripe is ~500ms. Don't let users double-click and create
two Checkout Sessions.

### 7.2. Secret Manager + Cloud Run env

Push secrets via gcloud:

```bash
for SECRET in STRIPE_PUBLISHABLE_KEY STRIPE_SECRET_KEY \
              STRIPE_WEBHOOK_SECRET; do
  printf '%s' "$STRIPE_VALUE" | gcloud secrets create "$SECRET" --data-file=- \
    || gcloud secrets versions add "$SECRET" --data-file=-
done
```

Add to Cloud Run service `wot-api`:
```bash
gcloud run services update wot-api --region=us-east1 \
  --set-secrets=STRIPE_SECRET_KEY=STRIPE_SECRET_KEY:latest,\
STRIPE_WEBHOOK_SECRET=STRIPE_WEBHOOK_SECRET:latest \
  --set-env-vars=STRIPE_PRICE_ID_PRO_MONTHLY=<price_id>,\
STRIPE_PRICE_ID_PRO_ANNUAL=<price_id>,\
STRIPE_PRICE_ID_PRO_OVERAGE=<price_id>
```

Frontend `wot-web` only needs the publishable key (and only if you
later add Stripe Elements; for hosted Checkout you don't even need
that). Skip for now.

### 7.3. Smoke test in Stripe test mode

1. Sign up a fresh test account on the staging deployment.
2. Click Subscribe Monthly. Use Stripe test card `4242 4242 4242 4242`.
3. Verify webhook fires; check `org.tier === 'pro'` in the DB.
4. Hit `/api/v1/search?q=hospital` 6,000 times in a minute.
   Verify the rate limiter lets all of them through (Pro = 5K/min...
   actually 5,001 is when it 429s. You're testing the right tier).
5. Hit `/api/v1/classify/demo` 250 times in one day. Verify only
   the first 200 succeed for Free; for Pro, verify all 250 succeed
   and the daily counter logs an overage of 50.
6. Run `scripts/push_classify_overage.py` against the test DB.
   Check Stripe dashboard: the test SubscriptionItem should show
   50 units of usage.
7. Open the Customer Portal via the dashboard button. Cancel.
   Verify webhook fires; check `org.tier === 'free'`.
8. Repeat steps 1-7 with Stripe test card `4000 0000 0000 0341`
   (declines on charge). Verify the trial start succeeds but the
   first invoice fails; verify your dunning email goes out.

End of Day 3 if all 8 smoke steps pass.

---

## 8. Things that will trip you up

1. **Stripe webhooks are at-least-once delivery.** Every event
   handler MUST be idempotent. The `processed_stripe_events`
   dedup pattern is non-negotiable.

2. **Test mode and live mode have separate Price IDs.** When you
   flip to live, the env vars in step 7.2 need updating.

3. **The trial period charges the card immediately for $0** to
   verify it; some users panic. Document this in the user-facing
   /pricing copy.

4. **Stripe metered usage has a 60-second granularity floor.**
   Don't push usage records every API call - batch daily.

5. **Customer Portal returns the user to your `return_url`
   regardless of whether they actually changed anything.** Your
   /developers/keys page needs to handle the "no-op return" case
   gracefully (don't show a "subscription updated!" toast unless
   you actually got a webhook event).

6. **Annual subscription cancellation gives the user a full year
   of Pro,** because you set portal config to "cancel at period
   end." Their `tier='pro'` until `tier_active_until`, then a
   daily cron flips them to free. Don't downgrade on
   `subscription.updated` - wait for the period to actually end.

7. **The metered Pro Overage Price MUST be on the SAME
   subscription as Pro Monthly/Annual.** That's why both line
   items go into one Checkout Session. If they're separate
   subscriptions, your usage push will fail with "no matching
   subscription_item" because Stripe can't infer the link.

8. **`stripe.api_key` is global state in the Python SDK.** Set it
   once at module import in `billing.py`; don't pass it per-call.

9. **`webhook.construct_event` is the ONLY safe way to parse
   Stripe webhooks.** Never `json.loads` the raw body and trust it -
   without signature validation, anyone can call your webhook
   endpoint and mark themselves as Pro.

10. **GDPR & data deletion**: when an org deletes their account,
    the org's Stripe Customer must also be deleted (or at least
    anonymized). The /privacy page promises this; honor it.

---

## 9. What to defer to v2

These are clearly desirable but explicitly out of scope for v1:

- **Hobbyist tier** ($9-19/mo between Free and Pro). Add only after
  Free → Pro conversion data exists.
- **Per-seat / team billing.** Today an org has one Pro subscription
  shared by all keys. Per-seat needs the team UI to ship first.
- **Graduated overage tiers** ($0.05 first 100, $0.02 next 1K, $0.01
  above). Single $0.05 rate is simpler and lets you collect data on
  who actually goes into overage before you complicate the pricing.
- **Annual prepay with custom volume**: "$0.04/call if you commit to
  100K/year upfront." Useful Enterprise tool; build when sales asks.
- **Crypto/Bitcoin payment.** Stripe doesn't natively support; not
  a real customer demand at our scale.
- **PayPal / wire transfer.** Stripe supports both; don't enable
  unless a customer asks. Each payment method adds dispute surface.
- **Gift cards / promo codes.** Stripe supports these; defer until
  you have a campaign that needs them.

---

## 10. Decisions only Ram can make

| Decision | When |
|---|---|
| Final go-live date for Stripe (test → live mode flip) | After soft launch, before public launch |
| Whether to enable annual prepay discount as default | Pre-launch (currently 17% off, default to monthly) |
| 14-day vs longer free trial | Pre-launch (locked at 14 days for v1) |
| Whether Enterprise is "Contact us" or has a $999/mo ceiling | Pre-launch (locked at "Contact us") |
| Refund policy text on /terms | Before public launch |

Don't proceed past test-mode if any of these are open.

---

## 11. Quick links

- Stripe Dashboard: https://dashboard.stripe.com/
- Stripe Python SDK docs: https://stripe.com/docs/api/python
- Stripe Webhook Events list: https://stripe.com/docs/api/events/types
- Stripe metered usage: https://stripe.com/docs/billing/subscriptions/usage-based
- Pricing source of truth: `.claude/.../memory/project_pricing_tiers.md`
- This doc: [stripe-integration.md](stripe-integration.md)
- Public-launch master list: [public-launch-todo.md](public-launch-todo.md)
- Marketing handover (says "Stripe not live yet"): [marketing-handover.md](marketing-handover.md)
- Schema (org table): [world_of_taxonomy/schema_devkeys.sql](../../world_of_taxonomy/schema_devkeys.sql)
- Existing tier reads: [world_of_taxonomy/api/deps.py](../../world_of_taxonomy/api/deps.py)

---

## 12. Day-zero checklist

- [ ] Confirm Stripe account access (use Colaberry's, or new one?)
- [ ] Read this doc end to end (~25 min)
- [ ] Read `.claude/.../memory/project_pricing_tiers.md` (~5 min)
- [ ] Confirm pricing decisions are still locked (check git log on
      the memory file; if it's been edited since 2026-05-04, talk to
      Ram before proceeding)
- [ ] Get Stripe test-mode API keys
- [ ] Schedule the 3-day block; this is contiguous work, not stop-start

After all checks pass, start Day 1. End-state: a Pro upgrade flow
working in production, tested end to end, with the metered overage
push running daily.
