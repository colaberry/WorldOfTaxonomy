#!/usr/bin/env python3
"""Push yesterday's per-org /classify overage to Stripe as Meter Events.

Runs as a Cloud Run Job triggered by Cloud Scheduler at ~03:00 UTC every
day. Reads `org_classify_usage` for yesterday, subtracts the included
Pro bucket (200/day), and reports the overage as a Meter Event keyed by
the org's stripe_customer_id. Stripe rolls these into the next monthly
invoice at $0.05/unit.

Idempotent: if it runs twice for the same day, the second run produces
the same Meter Events and Stripe deduplicates by event identifier.
That said, we set an explicit `identifier` per (org, day) so re-runs
are no-ops rather than accidental doubles.

Required env:
    DATABASE_URL                        - Cloud SQL connection string
    STRIPE_SECRET_KEY                   - Stripe secret key
    STRIPE_METER_EVENT_NAME             - default 'wot_classify_call'
    PRO_INCLUDED_DAILY_CLASSIFY         - default 200

Usage (one day, default = yesterday):
    python scripts/push_classify_overage.py

Backfill specific date:
    python scripts/push_classify_overage.py --date 2026-05-04
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import asyncpg
import stripe

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("push_classify_overage")


def _yesterday_utc() -> date:
    return date.today() - timedelta(days=1)


async def push_for_day(target_day: date, included_bucket: int) -> tuple[int, int, int]:
    """Push overage for the given day. Returns (orgs_seen, orgs_pushed, units_pushed)."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    event_name = os.environ.get("STRIPE_METER_EVENT_NAME", "wot_classify_call")

    conn = await asyncpg.connect(db_url)
    try:
        rows = await conn.fetch(
            """
            SELECT u.org_id, u.count, o.stripe_customer_id, o.tier
              FROM org_classify_usage u
              JOIN org o ON o.id = u.org_id
             WHERE u.usage_date = $1
               AND u.count > $2
               AND o.tier IN ('pro', 'enterprise')
               AND o.stripe_customer_id IS NOT NULL
            """,
            target_day,
            included_bucket,
        )
    finally:
        await conn.close()

    if not rows:
        log.info("no orgs with overage for %s; nothing to push", target_day)
        return (0, 0, 0)

    orgs_pushed = 0
    units_pushed = 0
    for row in rows:
        org_id = str(row["org_id"])
        customer_id = row["stripe_customer_id"]
        used = row["count"]
        overage = max(0, used - included_bucket)
        if overage <= 0:
            continue
        # Stable identifier so re-running for the same day does not
        # double-bill. Stripe dedups by identifier within a 24h window.
        identifier = f"classify-overage-{org_id}-{target_day.isoformat()}"
        try:
            stripe.billing.MeterEvent.create(
                event_name=event_name,
                payload={
                    "stripe_customer_id": customer_id,
                    "value": str(overage),
                },
                identifier=identifier,
            )
            orgs_pushed += 1
            units_pushed += overage
            log.info(
                "pushed %d units for org=%s customer=%s id=%s",
                overage,
                org_id,
                customer_id,
                identifier,
            )
        except Exception:
            log.exception(
                "failed to push meter event for org=%s customer=%s id=%s",
                org_id,
                customer_id,
                identifier,
            )

    return (len(rows), orgs_pushed, units_pushed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Push daily /classify overage to Stripe.")
    parser.add_argument(
        "--date",
        type=lambda s: date.fromisoformat(s),
        default=_yesterday_utc(),
        help="Day to push overage for (YYYY-MM-DD). Default: yesterday UTC.",
    )
    parser.add_argument(
        "--included-bucket",
        type=int,
        default=int(os.environ.get("PRO_INCLUDED_DAILY_CLASSIFY", "200")),
        help="Daily included classify-call quota; only counts above are billed. Default 200.",
    )
    args = parser.parse_args()

    log.info(
        "pushing classify overage for day=%s included_bucket=%d",
        args.date,
        args.included_bucket,
    )
    orgs_seen, orgs_pushed, units_pushed = asyncio.run(
        push_for_day(args.date, args.included_bucket)
    )
    log.info(
        "done: orgs_seen=%d orgs_pushed=%d units_pushed=%d",
        orgs_seen,
        orgs_pushed,
        units_pushed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
