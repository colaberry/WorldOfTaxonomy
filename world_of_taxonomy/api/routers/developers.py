"""Developer-facing endpoints for API key issuance and lifecycle.

Three flows:
  1. POST /api/v1/developers/signup
       Email-only signup. Mints a magic-link token, emails it, and
       (in dev mode) returns the link in the response so tests and
       local development do not need a real inbox.
  2. GET /api/v1/auth/magic-callback
       Single-use token consumption. Sets a `dev_session` cookie on
       the user's browser; redirects to /developers/keys.
  3. /api/v1/developers/keys
       Cookie-gated CRUD for the user's keys.

Designed for clean extraction to developer.aixcelerator.ai (Phase 7):
nothing in this file imports anything WoT-specific.
"""

from __future__ import annotations

import hmac
import json
import os
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from world_of_taxonomy.api.deps import get_conn, JWT_SECRET, JWT_ALGORITHM
from world_of_taxonomy.api.rate_guard import (
    _client_ip,
    check_email_send_budget,
    check_per_ip_rate,
    record_email_send,
)
from world_of_taxonomy.auth import keys as keys_mod
from world_of_taxonomy.auth import magic_link as ml
from world_of_taxonomy.auth import orgs
from world_of_taxonomy.auth.email import default_client, send_login_email


router = APIRouter(tags=["developers"])


# Config knobs


def _dev_mode() -> bool:
    """When true, signup endpoints leak the magic link in the response.

    Set DEV_KEYS_DEV_MODE=1 for local development and the test suite.
    Never enable in production - it makes signup a passwordless
    take-over of any email address.
    """
    return os.environ.get("DEV_KEYS_DEV_MODE", "").lower() in ("1", "true", "yes")


def _frontend_origin() -> str:
    return os.environ.get(
        "FRONTEND_ORIGIN", "https://worldoftaxonomy.com"
    ).rstrip("/")


def _session_ttl_minutes() -> int:
    return int(os.environ.get("DEV_SESSION_TTL_MINUTES", "60"))


# Request / response models


_EMAIL_RE = __import__("re").compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email")
        return v


class SignupResponse(BaseModel):
    detail: str
    magic_link_url: Optional[str] = None  # populated only in dev mode


class CreateKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: List[str] = Field(default_factory=lambda: ["wot:*"])
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=3650)


class KeyMetadata(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    revoked_at: Optional[str]


class KeyCreatedResponse(BaseModel):
    raw_key: str
    metadata: KeyMetadata


# Session cookie (short-lived JWT, separate from /api/v1/auth/* JWTs)


_DEV_SESSION_COOKIE = "dev_session"


def _mint_dev_session(user_id, org_id) -> str:
    payload = {
        "sub": str(user_id),
        "org": str(org_id),
        "kind": "dev_session",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=_session_ttl_minutes()),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_dev_session(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid session")
    if payload.get("kind") != "dev_session":
        raise HTTPException(status_code=401, detail="Invalid session")
    return payload


async def get_dev_session_user(
    dev_session: Optional[str] = Cookie(default=None),
    conn=Depends(get_conn),
) -> dict:
    """Resolve the dev_session cookie to a user record. 401 on miss."""
    if not dev_session:
        raise HTTPException(status_code=401, detail="dev_session cookie required")
    payload = _decode_dev_session(dev_session)
    try:
        user_uuid = _uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid session")
    row = await conn.fetchrow(
        """SELECT id, email, org_id, role
           FROM app_user WHERE id = $1""",
        user_uuid,
    )
    if row is None:
        raise HTTPException(status_code=401, detail="User not found")
    return dict(row)


# Endpoints: signup and magic-link


@router.post(
    "/api/v1/developers/signup",
    response_model=SignupResponse,
    status_code=202,
)
async def developers_signup(
    body: SignupRequest,
    request: Request,
    conn=Depends(get_conn),
):
    """Idempotent signup. Creates the user + org if new, then emails a
    magic link.

    Two abuse guards run BEFORE any DB write or email send:
      - per-IP cap (default 5/hour) catches a single source spamming
        random emails.
      - global email-send budget (default 200/hour, env-tunable via
        EMAIL_SEND_BUDGET_PER_HOUR) caps the Resend bill even if a
        botnet bypasses the per-IP cap.
    """
    check_per_ip_rate("developers_signup", request, max_per_window=5)
    await check_email_send_budget(conn)

    user = await orgs.signup_or_link(conn, body.email)
    raw_token = await ml.mint_token(conn, user["id"])
    magic_link_url = (
        f"{_frontend_origin()}/auth/magic?t={raw_token}"
    )
    try:
        send_login_email(
            client=default_client(),
            to=body.email,
            magic_link_url=magic_link_url,
        )
    except Exception:
        # Email infrastructure failure must not 500 a signup.
        # NoopEmailClient already logs; this catches Resend HTTP errors.
        pass

    # Record the send AFTER the email-client call. The next budget
    # check (above) will see this row.
    await record_email_send(
        conn,
        email=body.email,
        ip_address=_client_ip(request),
        purpose="magic_link",
    )

    payload = SignupResponse(
        detail="A sign-in link was sent to your email. It expires in 15 minutes.",
        magic_link_url=magic_link_url if _dev_mode() else None,
    )
    return payload


@router.get("/api/v1/auth/magic-callback")
async def auth_magic_callback(
    t: str,
    request: Request,
    response: Response,
    conn=Depends(get_conn),
):
    """Consume the magic-link token and set the dev_session cookie.

    Per-IP rate-limited at 30/min: tokens are 256-bit random, so
    flooding cannot guess one, but the limit caps DB cycles spent on
    failed lookups during a token-spray attack.
    """
    check_per_ip_rate(
        "auth_magic_callback", request, max_per_window=30, window_seconds=60,
    )
    user = await ml.consume_token(conn, t)
    if user is None:
        raise HTTPException(
            status_code=401, detail="Token is invalid, expired, or already used"
        )

    session = _mint_dev_session(user["user_id"], user["org_id"])
    response.set_cookie(
        _DEV_SESSION_COOKIE,
        session,
        max_age=_session_ttl_minutes() * 60,
        httponly=True,
        secure=os.environ.get("DEV_SESSION_INSECURE", "").lower() not in ("1", "true"),
        samesite="lax",
        path="/",
    )
    return {
        "detail": "Signed in",
        "redirect": f"{_frontend_origin()}/developers/keys",
    }


# Endpoints: key CRUD


@router.post(
    "/api/v1/developers/keys",
    response_model=KeyCreatedResponse,
    status_code=201,
)
async def create_key(
    body: CreateKeyRequest,
    user: dict = Depends(get_dev_session_user),
    conn=Depends(get_conn),
):
    try:
        minted = keys_mod.issue_key(body.scopes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    expires_at = None
    if body.expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    row = await conn.fetchrow(
        """INSERT INTO api_key
              (user_id, key_hash, key_prefix, name, scopes, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6)
           RETURNING id, name, key_prefix, scopes, created_at,
                     expires_at, last_used_at, revoked_at""",
        user["id"], minted["key_hash"], minted["key_prefix"],
        body.name, list(body.scopes), expires_at,
    )

    return KeyCreatedResponse(
        raw_key=minted["raw_key"],
        metadata=_key_metadata_from_row(row),
    )


@router.get(
    "/api/v1/developers/keys",
    response_model=List[KeyMetadata],
)
async def list_keys(
    user: dict = Depends(get_dev_session_user),
    conn=Depends(get_conn),
):
    rows = await conn.fetch(
        """SELECT id, name, key_prefix, scopes, created_at,
                  expires_at, last_used_at, revoked_at
           FROM api_key
           WHERE user_id = $1
           ORDER BY created_at DESC""",
        user["id"],
    )
    return [_key_metadata_from_row(r) for r in rows]


@router.delete("/api/v1/developers/keys/{key_id}")
async def revoke_key(
    key_id: str,
    user: dict = Depends(get_dev_session_user),
    conn=Depends(get_conn),
):
    try:
        key_uuid = _uuid.UUID(key_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid key id")

    row = await conn.fetchrow(
        """UPDATE api_key
              SET revoked_at = NOW(), revoked_reason = 'user_requested'
            WHERE id = $1 AND user_id = $2 AND revoked_at IS NULL
            RETURNING id, revoked_at""",
        key_uuid, user["id"],
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Key not found or already revoked")
    return {"id": str(row["id"]), "revoked_at": row["revoked_at"].isoformat()}


def _key_metadata_from_row(row) -> KeyMetadata:
    return KeyMetadata(
        id=str(row["id"]),
        name=row["name"],
        key_prefix=row["key_prefix"],
        scopes=list(row["scopes"]),
        created_at=row["created_at"].isoformat(),
        expires_at=row["expires_at"].isoformat() if row["expires_at"] else None,
        last_used_at=row["last_used_at"].isoformat() if row["last_used_at"] else None,
        revoked_at=row["revoked_at"].isoformat() if row["revoked_at"] else None,
    )
