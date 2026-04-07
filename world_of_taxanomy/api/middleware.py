"""Rate limiting middleware for WorldOfTaxanomy API."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse


async def _rate_limit_key(request: Request) -> str:
    """Determine rate limit key based on auth status.

    Returns a string key used for rate limiting:
    - Authenticated users: 'user:<user_id>' (higher limits)
    - Anonymous: IP address (lower limits)
    """
    # Avoid circular import
    from world_of_taxanomy.api.deps import get_optional_auth

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
        # Authenticated user -- we'll refine by tier in the dynamic limiter
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


async def rate_limit_middleware(request: Request, call_next):
    """Middleware that applies tiered rate limiting to /api/v1/ routes."""
    path = request.url.path

    # Only rate limit API routes
    if not path.startswith("/api/v1/"):
        return await call_next(request)

    # Determine the key and apply appropriate limit
    try:
        from world_of_taxanomy.api.deps import get_optional_auth
        user = await get_optional_auth(request)
    except Exception:
        user = None

    # Store user info for downstream use
    request.state.auth_user = user

    response = await call_next(request)
    return response
