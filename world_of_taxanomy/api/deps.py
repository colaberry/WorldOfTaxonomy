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


async def get_conn(request: Request):
    """Yield a database connection from the app's pool."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        yield conn


async def get_current_user(request: Request) -> dict:
    """Extract and validate JWT from Authorization header, return user record.

    Raises HTTPException 401 if token is missing or invalid.
    """
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
    """Check an API key against the database. Returns user record or None."""
    if not key.startswith("wot_") or len(key) != 36:
        return None

    key_prefix = key[4:12]  # first 8 chars after 'wot_'

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT ak.id AS api_key_id, ak.key_hash, ak.user_id, ak.is_active AS key_active,
                      au.id, au.email, au.display_name, au.tier, au.is_active
               FROM api_key ak
               JOIN app_user au ON ak.user_id = au.id
               WHERE ak.key_prefix = $1 AND ak.is_active = TRUE""",
            key_prefix,
        )

    for row in rows:
        key_bytes = key.encode("utf-8")
        stored_hash = row["key_hash"].encode("utf-8")
        if bcrypt.checkpw(key_bytes, stored_hash):
            if not row["is_active"]:
                return None
            # Update last_used_at
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
                "api_key_id": row["api_key_id"],
            }

    return None


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
