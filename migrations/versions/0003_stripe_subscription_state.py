"""Stripe subscription state on org + classify usage + webhook idempotency.

Revision ID: 0003_stripe_subscription_state
Revises: 0002_node_url_template
Create Date: 2026-05-06

Adds the columns the webhook handler needs to reflect the Stripe-side
subscription state on the org (so the rate limiter can read tier from
local DB without an extra Stripe API call per request) plus a small
table that tracks per-org per-day classify counts (the daily cron reads
this and pushes overage to Stripe Meter Events) plus a dedup table for
webhook event IDs (Stripe delivers at-least-once; handlers must be
idempotent).

Design notes:
- We do NOT need a `stripe_overage_meter_id` column. Stripe's Meter
  Event API attributes events by stripe_customer_id alone; no
  subscription-item lookup is needed.
- `tier_active_until` is set from `subscription.current_period_end`.
  A separate daily cron (not in this migration) flips tier='pro' ->
  'free' once `tier_active_until < now()`.
"""
from __future__ import annotations

from alembic import op


revision = "0003_stripe_subscription_state"
down_revision = "0002_node_url_template"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Subscription state on org. stripe_customer_id already exists
    # (provisioned in schema_devkeys.sql); we add the rest.
    op.execute(
        "ALTER TABLE org "
        "  ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT UNIQUE, "
        "  ADD COLUMN IF NOT EXISTS tier_active_until TIMESTAMPTZ"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_org_stripe_subscription "
        "  ON org(stripe_subscription_id) "
        "  WHERE stripe_subscription_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_org_tier_active_until "
        "  ON org(tier_active_until) "
        "  WHERE tier_active_until IS NOT NULL"
    )

    # 2. Per-org per-day classify call counter. Source of truth for the
    # daily Stripe Meter Event push. Keyed by org (not user) because the
    # subscription is at the org level. UPSERT pattern in code.
    op.execute(
        "CREATE TABLE IF NOT EXISTS org_classify_usage ("
        "  org_id     UUID NOT NULL REFERENCES org(id) ON DELETE CASCADE, "
        "  usage_date DATE NOT NULL DEFAULT CURRENT_DATE, "
        "  count      INTEGER NOT NULL DEFAULT 0, "
        "  PRIMARY KEY (org_id, usage_date)"
        ")"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_org_classify_usage_date "
        "  ON org_classify_usage(usage_date)"
    )

    # 3. Webhook event idempotency. Stripe delivers at-least-once;
    # without this dedup table a retry could process the same event
    # twice and double-bump tier or push duplicate meter events.
    op.execute(
        "CREATE TABLE IF NOT EXISTS processed_stripe_events ("
        "  event_id      TEXT PRIMARY KEY, "
        "  event_type    TEXT NOT NULL, "
        "  processed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        ")"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_processed_stripe_events_processed_at "
        "  ON processed_stripe_events(processed_at)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS processed_stripe_events")
    op.execute("DROP TABLE IF EXISTS org_classify_usage")
    op.execute("DROP INDEX IF EXISTS idx_org_tier_active_until")
    op.execute("DROP INDEX IF EXISTS idx_org_stripe_subscription")
    op.execute(
        "ALTER TABLE org "
        "  DROP COLUMN IF EXISTS tier_active_until, "
        "  DROP COLUMN IF EXISTS stripe_subscription_id"
    )
