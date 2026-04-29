"""Per-endpoint rate limits + global email-send budget guard.

The site-wide rate limiter (`api/middleware.py`) keys buckets on
org_id (authenticated) or IP (anonymous) and applies the same limit
to every endpoint. That is right for general API traffic but too
loose for abuse-prone endpoints:

  - /api/v1/developers/signup mints a magic-link email per call. A
    botnet can spam it with arbitrary addresses to drain the Resend
    budget. We need a per-IP-per-hour cap (single-source bots) AND a
    global-per-hour cap (distributed attacks).

  - /api/v1/auth/magic-callback consumes a 256-bit token. Tokens are
    unguessable, but a flood still consumes DB cycles. Per-IP-per-min
    cap is enough.

This module exposes two helpers:

  - `check_per_ip_rate(endpoint_name, request, per_hour)` raises 429
    when the caller's IP has already exceeded `per_hour` in the
    current rolling hour. In-process counter; one bucket per Cloud
    Run instance. Cheap, fast, no DB round-trip.

  - `check_email_send_budget(conn, max_per_hour)` raises 503 when the
    `email_send_log` table shows >= max_per_hour rows in the last
    hour. DB-backed; accurate across Cloud Run instances. Run BEFORE
    any expensive signup work.

  - `record_email_send(conn, email, ip_address, purpose)` writes the
    audit row. Call AFTER the email-client send returns; failure to
    record does not roll back the email.

Defaults are tuned conservatively so a polite legitimate burst does
not trip them. Override per endpoint with the function args.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import HTTPException, Request


# ---------- per-IP rate limit (in-process, hot path) -------------------------

# One deque per (endpoint, ip) holding monotonic timestamps in seconds. We
# evict timestamps older than the window when checking, so the deque is
# bounded by `per_hour`. Total memory is roughly:
#   N_endpoints x N_unique_ips_in_window x avg_requests_per_ip x 8 bytes
# At realistic soft-launch scale (say 5 endpoints, 10k unique IPs/hour, 10
# requests each), that is ~4 MB. Each Cloud Run instance starts empty.

_IP_HITS: Dict[str, Deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Honors X-Forwarded-For when present (Cloud
    Run sets this from the load balancer). Falls back to the socket peer.
    Returns the literal string 'unknown' when neither is available so the
    bucket key is still well-defined."""
    fwd = request.headers.get("x-forwarded-for", "").strip()
    if fwd:
        # First entry is the original client; the rest are proxies.
        return fwd.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def check_per_ip_rate(
    endpoint_name: str,
    request: Request,
    max_per_window: int,
    *,
    window_seconds: int = 3600,
) -> None:
    """Allow at most `max_per_window` requests from this IP to this
    endpoint in the trailing `window_seconds`. Raises 429 with a
    Retry-After header otherwise. Default window is one hour.

    Designed for endpoints that the site-wide limiter already covers
    but where a tighter cap matters (signup floods, magic-link callback
    spam). Uses an in-process LRU; per-instance counters are an
    intentional approximation - distributed attacks are caught by
    `check_email_send_budget`, which is DB-backed.
    """
    if max_per_window <= 0:
        return
    now = time.monotonic()
    cutoff = now - window_seconds
    key = f"{endpoint_name}:{_client_ip(request)}"
    bucket = _IP_HITS[key]
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= max_per_window:
        # Retry-After is the seconds until the oldest hit ages out of
        # the window, so a respectful client waits exactly that long.
        retry_after = max(1, int(bucket[0] + window_seconds - now))
        # Bump the abuse-signal counter so spikes are visible in
        # Prometheus / alerting before a human notices the 429s in logs.
        # Imported lazily to avoid a circular import (metrics module
        # imports rate_guard for the test stub).
        try:
            from world_of_taxonomy.api.metrics import RATE_GUARD_FIRED
            RATE_GUARD_FIRED.labels(endpoint=endpoint_name).inc()
        except Exception:
            # Metrics must never break a hot-path 429.
            pass
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "scope": f"per_ip:{endpoint_name}",
                "retry_after_seconds": retry_after,
                "message": (
                    f"Too many {endpoint_name} attempts from this IP. "
                    f"Try again in {retry_after} seconds."
                ),
            },
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


# ---------- global email-send budget (DB-backed) -----------------------------

def _hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


_DEFAULT_GLOBAL_CAP_ENV = "EMAIL_SEND_BUDGET_PER_HOUR"
_DEFAULT_GLOBAL_CAP = 200


def _resolve_cap(explicit: Optional[int]) -> int:
    if explicit is not None:
        return explicit
    raw = os.environ.get(_DEFAULT_GLOBAL_CAP_ENV, "").strip()
    if raw.isdigit():
        return int(raw)
    return _DEFAULT_GLOBAL_CAP


async def check_email_send_budget(
    conn,
    *,
    max_per_hour: Optional[int] = None,
) -> None:
    """Refuse the request with 503 when global email send count over the
    last hour is at or above the configured cap.

    DB-backed so the cap is enforced consistently across every Cloud Run
    instance. The query is a single index range scan on
    `idx_email_send_log_sent_at`; expected sub-millisecond.
    """
    cap = _resolve_cap(max_per_hour)
    if cap <= 0:
        return
    count = await conn.fetchval(
        """SELECT count(*)
           FROM email_send_log
           WHERE sent_at > NOW() - INTERVAL '1 hour'"""
    )
    if count is not None and count >= cap:
        try:
            from world_of_taxonomy.api.metrics import RATE_GUARD_FIRED
            RATE_GUARD_FIRED.labels(endpoint="email_send_budget").inc()
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail={
                "error": "email_budget_exhausted",
                "message": (
                    "Magic-link email volume is over the safety cap right "
                    "now. This usually clears within a few minutes; if it "
                    "does not, contact support."
                ),
            },
            headers={"Retry-After": "60"},
        )


async def record_email_send(
    conn,
    *,
    email: Optional[str],
    ip_address: Optional[str],
    purpose: str = "magic_link",
) -> None:
    """Append a row to `email_send_log`. Call AFTER the email client
    returns; insertion failures are swallowed so a transient DB blip
    does not make the user think signup failed."""
    if purpose not in ("magic_link", "key_issued", "key_revoked", "other"):
        purpose = "other"
    email_hash = _hash_email(email) if email else None
    try:
        await conn.execute(
            """INSERT INTO email_send_log (email_hash, ip_address, purpose)
               VALUES ($1, $2, $3)""",
            email_hash, ip_address, purpose,
        )
    except Exception:
        # Audit-only path; do not surface DB errors to the caller.
        pass


# ---------- testing helper ---------------------------------------------------

def _reset_for_tests() -> None:
    """Clear the in-process per-IP counters. Test fixtures call this so
    one test's hits do not bleed into the next."""
    _IP_HITS.clear()
