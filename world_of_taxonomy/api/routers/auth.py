"""Auth router -- /api/v1/auth endpoints.

Two sign-in flows ship today:

  - **OAuth** (GitHub, Google, LinkedIn) lives in `oauth.py` and mints
    a 15-minute JWT. The endpoints in this file (``/me``, ``/keys`` CRUD)
    consume that JWT.
  - **Magic-link** (email-only) lives in ``developers.py`` and issues a
    cookie session for the ``/developers/keys`` dashboard.

Password-based ``/register`` and ``/login`` were removed in 2026-04-30.
The bcrypt helpers, the credential-stuffing sliding-window guard
(``failed_auth.py``), and the ``RegisterRequest``/``LoginRequest``
schemas went with them. The ``app_user.password_hash`` column is left
in place (NULL for new users) so OAuth-flow inserts continue to match
the existing schema; a follow-up migration can drop it.
"""

from __future__ import annotations

import secrets
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import List

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request

from world_of_taxonomy.api.deps import get_conn, get_current_user, JWT_SECRET, JWT_ALGORITHM
from world_of_taxonomy.api.rate_guard import check_per_ip_rate
from world_of_taxonomy.api.schemas import (
    UserResponse,
    TokenResponse,
    CreateApiKeyRequest,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    UsageStatsResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = 15


def _create_access_token(user_id: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _user_response(row) -> UserResponse:
    """Convert a database row to UserResponse."""
    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        display_name=row["display_name"],
        tier=row["tier"],
        created_at=row["created_at"].isoformat(),
    )


def _api_key_response(row) -> ApiKeyResponse:
    """Convert a database row to ApiKeyResponse."""
    return ApiKeyResponse(
        id=str(row["id"]),
        key_prefix=row["key_prefix"],
        name=row["name"],
        is_active=row["is_active"],
        last_used_at=row["last_used_at"].isoformat() if row["last_used_at"] else None,
        created_at=row["created_at"].isoformat(),
        expires_at=row["expires_at"].isoformat() if row["expires_at"] else None,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, conn=Depends(get_conn)):
    """Get current user profile.

    Per-IP rate guard: 120/min via the shared `auth_session` bucket.
    Bounds loop attacks from a stolen JWT across /me + /keys CRUD
    without affecting interactive use.
    """
    check_per_ip_rate(
        "auth_session", request, max_per_window=120, window_seconds=60,
    )
    user = await get_current_user(request)
    row = await conn.fetchrow(
        "SELECT id, email, display_name, tier, created_at FROM app_user WHERE id = $1",
        user["id"],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_response(row)


@router.post("/keys", response_model=ApiKeyCreatedResponse)
async def create_api_key(body: CreateApiKeyRequest, request: Request, conn=Depends(get_conn)):
    """Create a new API key for the current user.

    Per-IP rate guard: 10/hour for key creation specifically. A stolen
    JWT minting many keys is a real abuse pattern; legitimate users
    create keys rarely. Shared `auth_session` cap (120/min) also
    applies via the get_current_user path on the second call.
    """
    check_per_ip_rate("auth_keys_create", request, max_per_window=10)
    user = await get_current_user(request)

    # Generate key: wot_ + 32 hex chars
    raw_key = "wot_" + secrets.token_hex(16)
    key_prefix = raw_key[4:12]
    key_hash = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    row = await conn.fetchrow(
        """INSERT INTO api_key (user_id, key_hash, key_prefix, name)
           VALUES ($1, $2, $3, $4)
           RETURNING id, key_prefix, name, is_active, last_used_at, created_at, expires_at""",
        user["id"],
        key_hash,
        key_prefix,
        body.name,
    )

    return ApiKeyCreatedResponse(
        key=raw_key,
        api_key=_api_key_response(row),
    )


@router.get("/keys", response_model=List[ApiKeyResponse])
async def list_api_keys(request: Request, conn=Depends(get_conn)):
    """List all API keys for the current user.

    Shares the `auth_session` bucket (120/min/IP).
    """
    check_per_ip_rate(
        "auth_session", request, max_per_window=120, window_seconds=60,
    )
    user = await get_current_user(request)

    rows = await conn.fetch(
        """SELECT id, key_prefix, name, is_active, last_used_at, created_at, expires_at
           FROM api_key
           WHERE user_id = $1
           ORDER BY created_at DESC""",
        user["id"],
    )

    return [_api_key_response(row) for row in rows]


@router.delete("/keys/{key_id}")
async def deactivate_api_key(key_id: str, request: Request, conn=Depends(get_conn)):
    """Deactivate an API key.

    Shares the `auth_session` bucket (120/min/IP).
    """
    check_per_ip_rate(
        "auth_session", request, max_per_window=120, window_seconds=60,
    )
    user = await get_current_user(request)

    try:
        key_uuid = _uuid.UUID(key_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid key ID format")

    result = await conn.execute(
        """UPDATE api_key SET is_active = FALSE
           WHERE id = $1 AND user_id = $2""",
        key_uuid,
        user["id"],
    )

    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="API key not found")

    return {"detail": "API key deactivated"}
