"""Dependency injection for FastAPI routes.

Provides database connections from the pool stored in app.state,
and authentication helpers.
"""

from __future__ import annotations

import os
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Request, HTTPException

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"

# When DISABLE_AUTH=true, auth endpoints return a synthetic dev user rather than
# raising 401. Set this in .env on development machines only.
DISABLE_AUTH = os.environ.get("DISABLE_AUTH", "").lower() in ("1", "true", "yes")

_DEV_USER: dict = {
    "id": None,
    "email": "dev@localhost",
    "display_name": "Dev User",
    "tier": "free",
    "is_active": True,
}


async def get_conn(request: Request):
    """Yield a database connection from the app's pool."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        yield conn


async def get_current_user(request: Request) -> dict:
    """Extract and validate JWT from Authorization header, return user record.

    Raises HTTPException 401 if token is missing or invalid.
    When DISABLE_AUTH=true (development only), always returns the synthetic dev user.
    """
    if DISABLE_AUTH:
        return _DEV_USER

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header[7:]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_uuid = _uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, display_name, tier, is_active, created_at FROM app_user WHERE id = $1",
            user_uuid,
        )

    if row is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    return dict(row)


async def validate_api_key(pool, key: str) -> Optional[dict]:
    """Check an API key against the database. Returns user record or None.

    Phase 6: returns the user record with org_id, scopes, and the
    rate-limit pool size from the org row, so middleware can key
    buckets without an extra round-trip. Honors revoked_at and
    expires_at; falls back to the legacy is_active=TRUE check for
    keys created before the migration.
    """
    if "_" not in key:
        return None
    underscore = key.index("_")
    key_prefix = key[underscore + 1 : underscore + 9]

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT ak.id AS api_key_id, ak.key_hash, ak.user_id,
                      ak.is_active AS key_active, ak.scopes,
                      ak.revoked_at, ak.expires_at,
                      au.id, au.email, au.display_name, au.tier,
                      au.is_active, au.org_id,
                      o.tier AS org_tier,
                      o.rate_limit_pool_per_minute
               FROM api_key ak
               JOIN app_user au ON ak.user_id = au.id
               LEFT JOIN org o ON au.org_id = o.id
               WHERE ak.key_prefix = $1 AND ak.revoked_at IS NULL""",
            key_prefix,
        )

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    for row in rows:
        if not bcrypt.checkpw(key.encode("utf-8"), row["key_hash"].encode("utf-8")):
            continue
        if not row["is_active"]:
            return None
        if row["expires_at"] is not None and row["expires_at"] <= now:
            return None
        # Update last_used_at on the hot path.
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE api_key SET last_used_at = NOW() WHERE id = $1",
                row["api_key_id"],
            )
        return {
            "id": row["id"],
            "email": row["email"],
            "display_name": row["display_name"],
            "tier": row["tier"],
            "org_id": row["org_id"],
            "org_tier": row["org_tier"],
            "rate_limit_pool_per_minute": row["rate_limit_pool_per_minute"],
            "scopes": list(row["scopes"]) if row["scopes"] else [],
            "api_key_id": row["api_key_id"],
        }

    return None


def require_scope(scope: str):
    """FastAPI dependency factory for `Depends(require_scope("wot:classify"))`.

    On a request without a valid key carrying `scope`:
      - 401 missing_api_key when no Authorization header (or wrong shape).
      - 401 invalid_api_key when the key did not validate.
      - 403 scope_missing when the key is valid but lacks `scope`.

    Each non-200 response carries the Phase 6 helpful headers
    (`WWW-Authenticate: ApiKey`, `Link: <...>; rel="signup"`) and a
    JSON body that points at /developers.
    """
    from world_of_taxonomy.auth import keys as keys_mod

    async def _dep(request: Request) -> dict:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise _missing_api_key_exception()
        raw = auth[7:].strip()

        pool = request.app.state.pool
        async with pool.acquire() as conn:
            result = await keys_mod.validate_key(conn, raw, required_scope=scope)

        if result["allow"]:
            return {
                "user_id": result["user_id"],
                "org_id": result["org_id"],
                "key_id": result["key_id"],
                "scopes": result["scopes"],
            }

        reason = result.get("reason")
        if reason == "scope_missing":
            raise _scope_missing_exception(scope)
        raise _invalid_api_key_exception(reason)

    return _dep


def _missing_api_key_exception() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "error": "missing_api_key",
            "message": (
                "API key required. Get a free key at "
                "https://worldoftaxonomy.com/developers"
            ),
            "anonymous_rate_limit": "30 req/min on public reads",
        },
        headers={
            "WWW-Authenticate": "ApiKey",
            "Link": '<https://worldoftaxonomy.com/developers>; rel="signup"',
        },
    )


def _invalid_api_key_exception(reason: Optional[str]) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "error": "invalid_api_key",
            "reason": reason or "not_found",
            "message": (
                "Your API key was not recognized. Manage keys at "
                "https://worldoftaxonomy.com/developers/keys"
            ),
        },
        headers={
            "WWW-Authenticate": "ApiKey",
            "Link": '<https://worldoftaxonomy.com/developers/keys>; rel="manage"',
        },
    )


def _scope_missing_exception(required: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "error": "scope_missing",
            "required_scope": required,
            "message": (
                f"Your key does not include {required}. Issue a new key "
                "with this scope at https://worldoftaxonomy.com/developers/keys"
            ),
        },
        headers={
            "Link": '<https://worldoftaxonomy.com/developers/keys>; rel="manage"',
        },
    )


async def get_optional_auth(request: Request) -> Optional[dict]:
    """Return user if JWT or API key present, None otherwise.

    Used for rate limit tier detection -- does not raise on missing auth.
    """
    # Try JWT first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        # Check if it looks like an API key
        if token.startswith("wot_"):
            user = await validate_api_key(request.app.state.pool, token)
            return user
        # Otherwise treat as JWT
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                try:
                    user_uuid = _uuid.UUID(user_id)
                except (ValueError, AttributeError):
                    return None
                pool = request.app.state.pool
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT id, email, display_name, tier, is_active FROM app_user WHERE id = $1",
                        user_uuid,
                    )
                if row and row["is_active"]:
                    return dict(row)
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass

    # Try X-API-Key header
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        user = await validate_api_key(request.app.state.pool, api_key)
        return user

    return None
