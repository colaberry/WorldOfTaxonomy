"""Rate limiting + security-headers + request-logging middleware for WorldOfTaxonomy API."""

from __future__ import annotations

import json
import logging
import os
import time
import uuid

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

_request_logger = logging.getLogger("wot.request")
_ACCESS_LOG_ENABLED = os.getenv("ACCESS_LOG", "true").lower() not in ("0", "false", "no")


async def request_id_middleware(request: Request, call_next):
    """Accept an incoming X-Request-ID or mint a new uuid4 for every request.

    Stores the id on request.state.request_id for downstream handlers
    and echoes it on the response so clients can correlate logs.
    Attaches the id to Sentry scope when Sentry is initialized.
    """
    incoming = request.headers.get("X-Request-ID", "").strip()
    request_id = incoming if incoming else uuid.uuid4().hex
    request.state.request_id = request_id

    try:
        import sentry_sdk

        sentry_sdk.set_tag("request_id", request_id)
    except Exception:
        pass

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def request_logging_middleware(request: Request, call_next):
    """Emit one JSON line per HTTP request.

    Includes method, path, status, duration_ms, user tier, and client IP.
    Disabled by setting ACCESS_LOG=false.
    """
    if not _ACCESS_LOG_ENABLED:
        return await call_next(request)

    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)

    user = getattr(request.state, "auth_user", None)
    record = {
        "request_id": getattr(request.state, "request_id", None),
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
        "ip": get_remote_address(request),
        "user_id": user.get("id") if user else None,
        "tier": user.get("tier") if user else "anonymous",
    }
    _request_logger.info(json.dumps(record, separators=(",", ":"), default=str))
    return response

# Security headers applied to every response. Kept conservative so the
# API and /docs Swagger UI both keep working.
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


async def security_headers_middleware(request: Request, call_next):
    """Attach baseline security headers to every response."""
    response = await call_next(request)
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    return response


# Per-minute rate limits by tier
TIER_RATE_LIMITS = {
    "anonymous": 30,
    "free": 100,
    "pro": 1000,
    "enterprise": 10000,
}

# Daily request caps by tier (None = unlimited)
TIER_DAILY_LIMITS = {
    "anonymous": 1000,
    "free": 5000,
    "pro": 100000,
    "enterprise": None,
}


async def _rate_limit_key(request: Request) -> str:
    """Determine rate limit key based on auth status.

    Returns a string key used for rate limiting:
    - Authenticated users: 'user:<user_id>' (higher limits)
    - Anonymous: IP address (lower limits)
    """
    # Avoid circular import
    from world_of_taxonomy.api.deps import get_optional_auth

    try:
        user = await get_optional_auth(request)
        if user:
            return "user:" + str(user["id"])
    except Exception:
        pass

    return get_remote_address(request)


def _get_rate_limit_string(key: str) -> str:
    """Return the rate limit string based on the key type."""
    if key.startswith("user:"):
        # Authenticated user - we'll refine by tier in the dynamic limiter
        return "1000/minute"
    return "30/minute"


# Create the limiter with IP-based default
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],
    storage_uri="memory://",
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down or authenticate for higher limits.",
            "retry_after": str(exc.detail),
        },
    )


async def _check_daily_limit(request: Request, user: dict | None) -> JSONResponse | None:
    """Check daily usage against tier limits. Returns 429 response if exceeded."""
    if user is None:
        # Anonymous daily limit checked by IP (skip for now - rate limit handles it)
        return None

    tier = user.get("tier", "free")
    daily_cap = TIER_DAILY_LIMITS.get(tier)
    if daily_cap is None:
        return None  # unlimited

    try:
        pool = request.app.state.pool
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                """SELECT count FROM daily_usage
                   WHERE user_id = $1 AND usage_date = CURRENT_DATE""",
                user["id"],
            )
            if count is not None and count >= daily_cap:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            f"Daily limit of {daily_cap:,} requests reached for {tier} tier. "
                            "Upgrade your plan at /developers for higher limits."
                        ),
                    },
                )
    except Exception:
        pass  # If daily_usage table doesn't exist yet, skip check

    return None


async def _increment_daily_usage(request: Request, user: dict | None) -> None:
    """Increment the daily usage counter for authenticated users."""
    if user is None:
        return

    try:
        pool = request.app.state.pool
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO daily_usage (user_id, usage_date, count)
                   VALUES ($1, CURRENT_DATE, 1)
                   ON CONFLICT (user_id, usage_date)
                   DO UPDATE SET count = daily_usage.count + 1""",
                user["id"],
            )
    except Exception:
        pass  # If table doesn't exist yet, skip silently


async def rate_limit_middleware(request: Request, call_next):
    """Middleware that applies tiered rate limiting to /api/v1/ routes."""
    path = request.url.path

    # Only rate limit API routes
    if not path.startswith("/api/v1/"):
        return await call_next(request)

    # Health checks must never be rate-limited so uptime probes
    # cannot knock themselves out.
    if path == "/api/v1/healthz":
        return await call_next(request)

    # Determine the key and apply appropriate limit
    try:
        from world_of_taxonomy.api.deps import get_optional_auth
        user = await get_optional_auth(request)
    except Exception:
        user = None

    # Store user info for downstream use
    request.state.auth_user = user

    # Check daily limit
    daily_exceeded = await _check_daily_limit(request, user)
    if daily_exceeded is not None:
        return daily_exceeded

    response = await call_next(request)

    # Increment daily usage counter on successful responses
    if response.status_code < 400:
        await _increment_daily_usage(request, user)

    return response
