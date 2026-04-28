"""One-time magic-link tokens for /developers sign-in.

Mint -> email -> consume. 15-minute TTL, single-use, server-side
nonce. SHA-256-hashed at rest so a database leak does not give the
attacker live login tokens.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Mapping, Optional


TOKEN_TTL = timedelta(minutes=15)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def mint_token(conn, user_id) -> str:
    """Generate, hash, and persist a fresh magic-link token.

    Returns the raw token. Email it to the user; never log or store
    it anywhere else.
    """
    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    expires_at = datetime.now(timezone.utc) + TOKEN_TTL
    await conn.execute(
        """INSERT INTO magic_link_token (user_id, token_hash, expires_at)
           VALUES ($1, $2, $3)""",
        user_id, token_hash, expires_at,
    )
    return raw


async def consume_token(conn, raw: str) -> Optional[Mapping]:
    """Atomically check + mark the token consumed.

    Returns the user record (id, email, org_id, role) on success.
    Returns None when the token is unknown, already consumed, or
    expired. The atomic UPDATE-with-RETURNING avoids the read-modify-
    write race two parallel clicks would otherwise hit.
    """
    if not raw:
        return None
    token_hash = _hash_token(raw)
    row = await conn.fetchrow(
        """UPDATE magic_link_token
              SET consumed_at = NOW()
            WHERE token_hash = $1
              AND consumed_at IS NULL
              AND expires_at > NOW()
            RETURNING user_id""",
        token_hash,
    )
    if row is None:
        return None
    user = await conn.fetchrow(
        "SELECT id AS user_id, email, org_id, role FROM app_user WHERE id = $1",
        row["user_id"],
    )
    return dict(user) if user else None
