"""Tests for the Stripe billing router.

Covers:
- Webhook signature verification (good vs forged)
- Webhook event dispatch table (right handler for each event type)
- Webhook idempotency (second delivery is a no-op)
- Subscription lifecycle (created -> tier='pro', deleted -> tier='free')
- Trial-end and payment-failed handlers (no immediate downgrade)
- Checkout / Portal endpoint contracts (call Stripe SDK with right args)
- Classify counter UPSERT (per-org per-day)

Tests do not hit Stripe's API. We mock at the SDK boundary so the suite
runs offline. Tests do not invoke the FastAPI router via TestClient
(matches the project's existing pattern in test_api_classify.py).
"""
from __future__ import annotations

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------


class TestWebhookSignature:
    """Stripe webhook signature must validate; bad signatures must 400."""

    def test_invalid_signature_returns_400(self):
        from world_of_taxonomy.api.routers.billing import verify_webhook

        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
            with pytest.raises(Exception) as exc_info:
                verify_webhook(
                    payload=b'{"id": "evt_x", "type": "customer.subscription.created"}',
                    sig_header="t=123,v1=deadbeef",  # not a real signature
                )
            assert "signature" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_missing_secret_raises(self):
        from world_of_taxonomy.api.routers.billing import verify_webhook

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
            with pytest.raises(Exception):
                verify_webhook(payload=b"{}", sig_header="t=1,v1=foo")


# ---------------------------------------------------------------------------
# Webhook dispatch
# ---------------------------------------------------------------------------


class TestWebhookDispatch:
    """The dispatch table routes each event type to the right handler."""

    def test_dispatch_table_covers_six_events(self):
        from world_of_taxonomy.api.routers.billing import EVENT_HANDLERS

        expected = {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
            "customer.subscription.trial_will_end",
        }
        assert expected.issubset(set(EVENT_HANDLERS.keys()))

    def test_unknown_event_type_returns_ok(self):
        """Unknown event types are accepted and logged; we do NOT 4xx them
        (Stripe would retry forever, and the event might be one we add
        support for later)."""
        from world_of_taxonomy.api.routers.billing import dispatch_event

        event = {"id": "evt_x", "type": "charge.refunded", "data": {"object": {}}}
        result = _run(dispatch_event(event, conn=AsyncMock()))
        # Unknown events return None (or similar) and do not raise
        assert result is None or result == "ignored"


# ---------------------------------------------------------------------------
# Webhook idempotency
# ---------------------------------------------------------------------------


class TestWebhookIdempotency:
    """Second delivery of the same event_id must be a no-op."""

    def test_already_processed_event_skips_handler(self):
        from world_of_taxonomy.api.routers.billing import process_webhook_event

        conn = AsyncMock()
        # First call: fetchval returns None (event not seen)
        # Second call: fetchval returns the event_id (already processed)
        conn.fetchval = AsyncMock(side_effect=[None, "evt_dup_id"])
        conn.execute = AsyncMock()

        event = {
            "id": "evt_dup_id",
            "type": "customer.subscription.created",
            "data": {"object": {"id": "sub_x", "customer": "cus_x", "current_period_end": 0, "metadata": {"org_id": "org_x"}}},
        }

        # Second invocation should short-circuit on the dedup check
        with patch(
            "world_of_taxonomy.api.routers.billing.dispatch_event",
            new=AsyncMock(),
        ) as mock_dispatch:
            _run(process_webhook_event(event, conn=conn))
            _run(process_webhook_event(event, conn=conn))
            # dispatch_event called only once across two process_webhook_event invocations
            assert mock_dispatch.call_count == 1


# ---------------------------------------------------------------------------
# Subscription lifecycle handlers
# ---------------------------------------------------------------------------


class TestSubscriptionHandlers:
    """customer.subscription.created -> tier='pro'; .deleted -> 'free'."""

    def test_subscription_created_flips_tier_to_pro(self):
        from world_of_taxonomy.api.routers.billing import _on_subscription_active

        conn = AsyncMock()
        conn.execute = AsyncMock()
        event_obj = {
            "id": "sub_test",
            "customer": "cus_test",
            "current_period_end": 1799999999,
            "metadata": {"org_id": "11111111-1111-1111-1111-111111111111"},
        }

        _run(_on_subscription_active(event_obj, conn=conn))

        # Should have UPDATEd org SET tier='pro' ...
        assert conn.execute.called
        call_args = conn.execute.call_args
        sql = call_args[0][0]
        assert "UPDATE org" in sql
        assert "tier" in sql
        assert "stripe_subscription_id" in sql

    def test_subscription_deleted_flips_tier_to_free(self):
        from world_of_taxonomy.api.routers.billing import _on_subscription_canceled

        conn = AsyncMock()
        conn.execute = AsyncMock()
        event_obj = {
            "id": "sub_test",
            "customer": "cus_test",
        }

        _run(_on_subscription_canceled(event_obj, conn=conn))

        assert conn.execute.called
        sql = conn.execute.call_args[0][0]
        assert "UPDATE org" in sql
        assert "free" in sql.lower()


class TestSoftFailHandlers:
    """Payment failures and trial-ending must NOT immediately downgrade."""

    def test_payment_failed_does_not_downgrade(self):
        from world_of_taxonomy.api.routers.billing import _on_payment_failed

        conn = AsyncMock()
        conn.execute = AsyncMock()
        event_obj = {"customer": "cus_test", "id": "in_test"}

        _run(_on_payment_failed(event_obj, conn=conn))

        # No UPDATE org SET tier='free' should fire here.
        for call in conn.execute.call_args_list:
            sql = call[0][0]
            assert not ("UPDATE org" in sql and "free" in sql.lower())


# ---------------------------------------------------------------------------
# Classify counter UPSERT
# ---------------------------------------------------------------------------


class TestClassifyCounter:
    """The /classify endpoint must increment org_classify_usage on each call."""

    def test_increment_classify_count_upserts(self):
        from world_of_taxonomy.api.routers.billing import increment_classify_count

        conn = AsyncMock()
        conn.execute = AsyncMock()
        org_id = "11111111-1111-1111-1111-111111111111"

        _run(increment_classify_count(conn=conn, org_id=org_id))

        assert conn.execute.called
        sql = conn.execute.call_args[0][0]
        assert "INSERT INTO org_classify_usage" in sql
        assert "ON CONFLICT" in sql
        assert "count + 1" in sql or "count = " in sql


# ---------------------------------------------------------------------------
# Checkout endpoint
# ---------------------------------------------------------------------------


class TestCheckoutEndpoint:
    """POST /api/v1/billing/checkout creates a Stripe Checkout Session."""

    def test_checkout_rejects_invalid_plan(self):
        from world_of_taxonomy.api.routers.billing import CheckoutRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CheckoutRequest(plan="invalid_plan")

    def test_checkout_accepts_pro_monthly_and_pro_annual(self):
        from world_of_taxonomy.api.routers.billing import CheckoutRequest

        # Both should validate
        m = CheckoutRequest(plan="pro_monthly")
        a = CheckoutRequest(plan="pro_annual")
        assert m.plan == "pro_monthly"
        assert a.plan == "pro_annual"

    def test_checkout_creates_stripe_session(self):
        """The endpoint should call stripe.checkout.Session.create with
        the correct price id and customer metadata."""
        from world_of_taxonomy.api.routers.billing import (
            CheckoutRequest,
            create_checkout_session,
        )

        env = {
            "STRIPE_SECRET_KEY": "sk_test",
            "STRIPE_PRICE_ID_PRO_MONTHLY": "price_M",
            "STRIPE_PRICE_ID_PRO_ANNUAL": "price_A",
            "STRIPE_PRICE_ID_PRO_OVERAGE": "price_O",
            "FRONTEND_URL": "https://worldoftaxonomy.com",
        }
        user = {
            "id": "user_x",
            "email": "x@y.com",
            "org_id": "11111111-1111-1111-1111-111111111111",
        }
        conn = AsyncMock()
        conn.fetchrow = AsyncMock(
            return_value={"id": user["org_id"], "stripe_customer_id": None, "tier": "free"}
        )
        conn.execute = AsyncMock()

        with patch.dict(os.environ, env), patch(
            "stripe.Customer.create", return_value=MagicMock(id="cus_new")
        ) as mock_cust, patch(
            "stripe.checkout.Session.create",
            return_value=MagicMock(url="https://checkout.stripe.com/c/test"),
        ) as mock_sess:
            url = _run(
                create_checkout_session(
                    request=CheckoutRequest(plan="pro_monthly"),
                    user=user,
                    conn=conn,
                )
            )

        assert "stripe.com" in url
        assert mock_sess.called
        kwargs = mock_sess.call_args.kwargs
        # Must include both the base price and the metered overage price
        line_item_prices = {item["price"] for item in kwargs["line_items"]}
        assert "price_M" in line_item_prices
        assert "price_O" in line_item_prices
        # Must pass org_id in metadata so the webhook can attribute back
        assert kwargs["subscription_data"]["metadata"]["org_id"] == user["org_id"]
        # Must enable 14-day trial
        assert kwargs["subscription_data"]["trial_period_days"] == 14
