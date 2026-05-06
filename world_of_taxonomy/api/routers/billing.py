"""Stripe billing endpoints + webhook handler.

Three HTTP endpoints:
- POST /api/v1/billing/checkout : create a Stripe Checkout Session and
                                  return its hosted URL (cookie-gated)
- POST /api/v1/billing/portal   : create a Customer Portal Session and
                                  return its hosted URL (cookie-gated)
- POST /api/v1/billing/webhook  : receive Stripe events, validate the
                                  signature, dispatch to handlers
                                  (NOT cookie-gated; signature is the
                                  authentication)

Plus internal helpers used by other modules:
- increment_classify_count    : called by /classify on every successful
                                pro/enterprise call; UPSERTs the daily
                                counter that the overage cron reads
- verify_webhook              : signature verification wrapper around
                                stripe.Webhook.construct_event (so the
                                test suite can exercise it without
                                instantiating the full FastAPI request)
- process_webhook_event       : idempotency wrapper around dispatch_event
- dispatch_event              : routes events to per-type handlers

Pricing decisions baked in here are sourced from
project_pricing_tiers.md (locked 2026-05-04). Do not freelance the
numbers; change the memory entry first if a price changes.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Awaitable, Callable, Literal, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from world_of_taxonomy.api.deps import get_conn, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Set the stripe.api_key once at import. Stripe SDK uses module-global state.
# In tests we patch this; in production it's set via Cloud Run secret.
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    plan: Literal["pro_monthly", "pro_annual"]


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class BillingStateResponse(BaseModel):
    tier: Literal["free", "pro", "enterprise"]
    tier_active_until: Optional[str] = None  # ISO 8601 if set
    classify_today_count: int
    has_stripe_customer: bool


# ---------------------------------------------------------------------------
# Webhook signature verification + idempotency
# ---------------------------------------------------------------------------


def verify_webhook(payload: bytes, sig_header: str) -> dict[str, Any]:
    """Validate the Stripe-Signature header and return the parsed event.

    Raises stripe.error.SignatureVerificationError (or the generic
    ValueError it catches internally) on bad signatures. The caller in
    the FastAPI route turns those into HTTP 400.
    """
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError(
            "STRIPE_WEBHOOK_SECRET is not set; webhook signatures cannot be verified."
        )
    return stripe.Webhook.construct_event(payload, sig_header, secret)


async def process_webhook_event(event: dict[str, Any], conn: Any) -> None:
    """Idempotency-checked dispatch.

    Looks up the event_id in processed_stripe_events; if it already
    exists, skip. Otherwise dispatch and record. On dispatch failure
    we leave the row absent so Stripe retries (and our handler runs
    again with a chance to succeed).
    """
    event_id = event["id"]
    seen = await conn.fetchval(
        "SELECT event_id FROM processed_stripe_events WHERE event_id = $1",
        event_id,
    )
    if seen:
        logger.info("stripe webhook %s already processed; skipping", event_id)
        return

    await dispatch_event(event, conn=conn)

    await conn.execute(
        "INSERT INTO processed_stripe_events (event_id, event_type) "
        "VALUES ($1, $2) "
        "ON CONFLICT (event_id) DO NOTHING",
        event_id,
        event["type"],
    )


# ---------------------------------------------------------------------------
# Per-event handlers
# ---------------------------------------------------------------------------


async def _on_subscription_active(obj: dict[str, Any], conn: Any) -> None:
    """customer.subscription.{created,updated} -> tier='pro' on the org.

    We look up the org by the metadata.org_id we set in Checkout. The
    subscription's current_period_end becomes our tier_active_until.
    """
    org_id = (obj.get("metadata") or {}).get("org_id")
    sub_id = obj.get("id")
    customer_id = obj.get("customer")
    period_end = obj.get("current_period_end")  # unix seconds

    if not org_id:
        logger.warning(
            "stripe subscription %s has no metadata.org_id; cannot attribute",
            sub_id,
        )
        return

    await conn.execute(
        "UPDATE org "
        "   SET tier = 'pro', "
        "       stripe_customer_id = COALESCE(stripe_customer_id, $2), "
        "       stripe_subscription_id = $3, "
        "       tier_active_until = TO_TIMESTAMP($4) "
        " WHERE id = $1",
        org_id,
        customer_id,
        sub_id,
        period_end,
    )


async def _on_subscription_canceled(obj: dict[str, Any], conn: Any) -> None:
    """customer.subscription.deleted -> tier='free' on the org.

    Triggered when Stripe finalizes a cancellation (after the period
    ends if the user clicked cancel-at-period-end, or immediately if
    Stripe gave up after dunning). Keep stripe_customer_id so the
    user can re-subscribe.
    """
    sub_id = obj.get("id")
    customer_id = obj.get("customer")

    await conn.execute(
        "UPDATE org "
        "   SET tier = 'free', "
        "       stripe_subscription_id = NULL, "
        "       tier_active_until = NULL "
        " WHERE stripe_subscription_id = $1 "
        "    OR stripe_customer_id = $2",
        sub_id,
        customer_id,
    )


async def _on_payment_succeeded(obj: dict[str, Any], conn: Any) -> None:
    """invoice.payment_succeeded -> nothing to do here.

    The next customer.subscription.updated event will carry the new
    period_end and we'll extend tier_active_until from there. Logged
    for ops visibility.
    """
    logger.info(
        "stripe invoice %s payment succeeded for customer %s",
        obj.get("id"),
        obj.get("customer"),
    )


async def _on_payment_failed(obj: dict[str, Any], conn: Any) -> None:
    """invoice.payment_failed -> log and notify; DO NOT downgrade.

    Stripe will retry dunning for ~3 weeks. If it gives up,
    customer.subscription.deleted will fire and _on_subscription_canceled
    handles the actual downgrade. Until then the user keeps Pro.

    TODO(post-launch): wire Resend email here ("your payment failed").
    """
    logger.warning(
        "stripe invoice %s payment FAILED for customer %s; dunning in progress",
        obj.get("id"),
        obj.get("customer"),
    )


async def _on_trial_ending(obj: dict[str, Any], conn: Any) -> None:
    """customer.subscription.trial_will_end -> notify the user.

    Stripe sends this 3 days before the 14-day trial ends.

    TODO(post-launch): wire Resend email here ("your trial ends in 3 days").
    """
    logger.info(
        "stripe trial ending for customer %s, subscription %s",
        obj.get("customer"),
        obj.get("id"),
    )


EventHandler = Callable[[dict[str, Any], Any], Awaitable[None]]
EVENT_HANDLERS: dict[str, EventHandler] = {
    "customer.subscription.created": _on_subscription_active,
    "customer.subscription.updated": _on_subscription_active,
    "customer.subscription.deleted": _on_subscription_canceled,
    "invoice.payment_succeeded": _on_payment_succeeded,
    "invoice.payment_failed": _on_payment_failed,
    "customer.subscription.trial_will_end": _on_trial_ending,
}


async def dispatch_event(event: dict[str, Any], conn: Any) -> Optional[str]:
    """Route a webhook event to its handler.

    Returns None on success. Returns 'ignored' for unknown event types
    (we still 200 them so Stripe stops retrying; we may add support
    later).
    """
    event_type = event.get("type", "")
    handler = EVENT_HANDLERS.get(event_type)
    if handler is None:
        logger.info("stripe webhook %s ignored (no handler)", event_type)
        return "ignored"
    obj = event.get("data", {}).get("object", {})
    await handler(obj, conn=conn)
    return None


# ---------------------------------------------------------------------------
# Classify counter (called by classify.py on every Pro/Enterprise call)
# ---------------------------------------------------------------------------


async def increment_classify_count(conn: Any, org_id: str) -> None:
    """UPSERT today's counter for this org by 1.

    Source of truth for the daily Stripe Meter Event push (cron in
    scripts/push_classify_overage.py).
    """
    await conn.execute(
        "INSERT INTO org_classify_usage (org_id, usage_date, count) "
        "VALUES ($1, CURRENT_DATE, 1) "
        "ON CONFLICT (org_id, usage_date) "
        "DO UPDATE SET count = org_classify_usage.count + 1",
        org_id,
    )


# ---------------------------------------------------------------------------
# Endpoint: POST /api/v1/billing/checkout
# ---------------------------------------------------------------------------


def _frontend_url() -> str:
    return os.environ.get("FRONTEND_URL", "https://worldoftaxonomy.com").rstrip("/")


def _price_id_for_plan(plan: str) -> str:
    if plan == "pro_monthly":
        pid = os.environ.get("STRIPE_PRICE_ID_PRO_MONTHLY")
    elif plan == "pro_annual":
        pid = os.environ.get("STRIPE_PRICE_ID_PRO_ANNUAL")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan}")
    if not pid:
        raise HTTPException(
            status_code=503,
            detail=f"Stripe price for {plan} is not configured.",
        )
    return pid


def _overage_price_id() -> str:
    pid = os.environ.get("STRIPE_PRICE_ID_PRO_OVERAGE")
    if not pid:
        raise HTTPException(
            status_code=503,
            detail="Stripe overage price is not configured.",
        )
    return pid


async def create_checkout_session(
    request: CheckoutRequest,
    user: dict,
    conn: Any,
) -> str:
    """Create a Checkout Session and return its hosted URL.

    Lifts the work out of the FastAPI handler so tests can drive it
    directly. The HTTP route below is a thin wrapper.
    """
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no org.")

    org = await conn.fetchrow(
        "SELECT id, stripe_customer_id, tier FROM org WHERE id = $1",
        org_id,
    )
    if not org:
        raise HTTPException(status_code=404, detail="Org not found.")

    if org["tier"] == "pro":
        raise HTTPException(
            status_code=409,
            detail="This org already has an active Pro subscription.",
        )

    # Get-or-create the Stripe Customer for this org.
    customer_id = org["stripe_customer_id"]
    if not customer_id:
        cust = stripe.Customer.create(
            email=user.get("email"),
            metadata={"org_id": org_id},
        )
        customer_id = cust.id
        await conn.execute(
            "UPDATE org SET stripe_customer_id = $1 WHERE id = $2",
            customer_id,
            org_id,
        )

    base_price = _price_id_for_plan(request.plan)
    overage_price = _overage_price_id()
    base_url = _frontend_url()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[
            {"price": base_price, "quantity": 1},
            {"price": overage_price},  # metered: no quantity
        ],
        subscription_data={
            "trial_period_days": 14,
            "metadata": {"org_id": str(org_id)},
        },
        success_url=f"{base_url}/developers/keys?upgraded=true",
        cancel_url=f"{base_url}/pricing?canceled=true",
        allow_promotion_codes=True,
    )
    return session.url


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout_endpoint(
    body: CheckoutRequest,
    user: dict = Depends(get_current_user),
    conn=Depends(get_conn),
):
    url = await create_checkout_session(body, user=user, conn=conn)
    return {"checkout_url": url}


# ---------------------------------------------------------------------------
# Endpoint: POST /api/v1/billing/portal
# ---------------------------------------------------------------------------


@router.post("/portal", response_model=PortalResponse)
async def portal_endpoint(
    user: dict = Depends(get_current_user),
    conn=Depends(get_conn),
):
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no org.")

    customer_id = await conn.fetchval(
        "SELECT stripe_customer_id FROM org WHERE id = $1",
        org_id,
    )
    if not customer_id:
        raise HTTPException(
            status_code=404,
            detail="No Stripe customer for this org.",
        )

    base_url = _frontend_url()
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{base_url}/developers/keys",
    )
    return {"portal_url": session.url}


# ---------------------------------------------------------------------------
# Endpoint: POST /api/v1/billing/webhook
# ---------------------------------------------------------------------------


@router.post("/webhook", include_in_schema=False)
async def webhook_endpoint(request: Request, conn=Depends(get_conn)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = verify_webhook(payload=payload, sig_header=sig_header)
    except Exception as exc:  # SignatureVerificationError, ValueError, etc.
        logger.warning("stripe webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature.")

    try:
        await process_webhook_event(event, conn=conn)
    except Exception:
        # Re-raise as 500 so Stripe retries. But log first so we have
        # the event_id when we debug.
        logger.exception("stripe webhook handler failed for event %s", event.get("id"))
        raise

    return {"ok": True}


# ---------------------------------------------------------------------------
# Endpoint: GET /api/v1/billing/state (cookie-gated)
# ---------------------------------------------------------------------------


@router.get("/state", response_model=BillingStateResponse)
async def state_endpoint(
    user: dict = Depends(get_current_user),
    conn=Depends(get_conn),
):
    """Return the org's current billing state for the dashboard panel."""
    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no org.")

    row = await conn.fetchrow(
        "SELECT tier, tier_active_until, stripe_customer_id "
        "  FROM org WHERE id = $1",
        org_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Org not found.")

    classify_today = await conn.fetchval(
        "SELECT count FROM org_classify_usage "
        " WHERE org_id = $1 AND usage_date = CURRENT_DATE",
        org_id,
    )

    until = row["tier_active_until"]
    return {
        "tier": row["tier"],
        "tier_active_until": until.isoformat() if until else None,
        "classify_today_count": int(classify_today or 0),
        "has_stripe_customer": bool(row["stripe_customer_id"]),
    }
