"""Auth router -- /api/v1/auth endpoints."""

from __future__ import annotations

import asyncio
import os
import secrets
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import List

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request

from world_of_taxonomy.api.deps import get_conn, get_current_user, JWT_SECRET, JWT_ALGORITHM
from world_of_taxonomy.api.rate_guard import check_per_ip_rate
from world_of_taxonomy.api.failed_auth import (
    check_blocked,
    mark_lockout,
    record_failure,
    record_success,
)
from world_of_taxonomy.api.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
    CreateApiKeyRequest,
    ApiKeyResponse,
    ApiKeyCreatedResponse,
    UsageStatsResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = 15


def _hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


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


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, request: Request, conn=Depends(get_conn)):
    """Register a new user account.

    Per-IP rate guard: 5/hour. Each registration mints a JWT, writes to
    app_user, and fires a webhook - cheap to abuse, expensive to clean
    up. The cap is the same as /developers/signup since the abuse
    surface is identical (user enumeration + webhook spam).
    """
    check_per_ip_rate("auth_register", request, max_per_window=5)
    # Check if email already exists
    existing = await conn.fetchrow(
        "SELECT id FROM app_user WHERE email = $1", body.email
    )
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Validate password length
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    password_hash = _hash_password(body.password)

    row = await conn.fetchrow(
        """INSERT INTO app_user (email, password_hash, display_name)
           VALUES ($1, $2, $3)
           RETURNING id""",
        body.email,
        password_hash,
        body.display_name,
    )

    access_token = _create_access_token(str(row["id"]))

    # Notify via webhook (fire-and-forget)
    from world_of_taxonomy.webhook import send_webhook
    asyncio.create_task(
        send_webhook("new_registration", {
            "email": body.email,
            "display_name": body.display_name,
        })
    )

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, conn=Depends(get_conn)):
    """Login with email and password.

    Failed attempts are tracked in a sliding window keyed by source IP
    and target email; repeated failures return 429 to blunt credential
    stuffing. Successful logins clear the counters for that IP+email.
    """
    ip = request.client.host if request.client else "unknown"
    blocked, reason = check_blocked(ip, body.email)
    if blocked:
        mark_lockout(reason or "ip")
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Try again later.",
        )

    row = await conn.fetchrow(
        "SELECT id, password_hash, is_active, oauth_provider FROM app_user WHERE email = $1",
        body.email,
    )
    if row is None:
        record_failure(ip, body.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    if row["password_hash"] is None:
        raise HTTPException(
            status_code=401,
            detail="This account uses social login. Please sign in with GitHub, Google, or LinkedIn.",
        )
    if not _verify_password(body.password, row["password_hash"]):
        record_failure(ip, body.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    record_success(ip, body.email)
    access_token = _create_access_token(str(row["id"]))
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, conn=Depends(get_conn)):
    """Get current user profile."""
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
    """Create a new API key for the current user."""
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
    """List all API keys for the current user."""
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
    """Deactivate an API key."""
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
