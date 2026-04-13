"""OAuth 2.0 social login - GitHub, Google, LinkedIn.

GET /api/v1/auth/oauth/{provider}/authorize  - get provider redirect URL
GET /api/v1/auth/oauth/{provider}/callback   - handle OAuth callback, issue JWT

Flow:
  1. Frontend calls /authorize, gets back {"auth_url": "...", "provider": "..."}
  2. Frontend redirects the user to auth_url
  3. Provider redirects to /callback?code=...&state=...
  4. Backend exchanges code, fetches profile, upserts user, issues JWT
  5. Backend redirects to frontend with ?token=<jwt>&email=...&name=...
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from world_of_taxanomy.api.deps import get_conn, JWT_SECRET, JWT_ALGORITHM

router = APIRouter(prefix="/api/v1/auth/oauth", tags=["oauth"])

# ── Provider config ──────────────────────────────────────────────────────────

_PROVIDERS: dict[str, dict] = {
    "github": {
        "auth_url":    "https://github.com/login/oauth/authorize",
        "token_url":   "https://github.com/login/oauth/access_token",
        "profile_url": "https://api.github.com/user",
        "emails_url":  "https://api.github.com/user/emails",
        "scope":       "user:email read:user",
        "client_id_env":     "GITHUB_CLIENT_ID",
        "client_secret_env": "GITHUB_CLIENT_SECRET",
    },
    "google": {
        "auth_url":    "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url":   "https://oauth2.googleapis.com/token",
        "profile_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope":       "openid email profile",
        "client_id_env":     "GOOGLE_CLIENT_ID",
        "client_secret_env": "GOOGLE_CLIENT_SECRET",
    },
    "linkedin": {
        "auth_url":    "https://www.linkedin.com/oauth/v2/authorization",
        "token_url":   "https://www.linkedin.com/oauth/v2/accessToken",
        "profile_url": "https://api.linkedin.com/v2/userinfo",
        "scope":       "openid profile email",
        "client_id_env":     "LINKEDIN_CLIENT_ID",
        "client_secret_env": "LINKEDIN_CLIENT_SECRET",
    },
}

_BACKEND_URL  = os.environ.get("BACKEND_URL",  "http://localhost:8000")
_FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# OAuth JWT lifetime - longer than API JWTs since there is no password to
# re-verify; users can revoke by clearing local storage.
_OAUTH_TOKEN_EXPIRE_DAYS = 30

# ── State helpers ────────────────────────────────────────────────────────────


def _make_state(redirect_to: str) -> str:
    """Return a signed JWT to use as the OAuth state parameter.

    Encodes redirect_to + a random nonce so the callback can recover the
    destination URL and is protected against CSRF.
    """
    payload = {
        "nonce":       secrets.token_hex(16),
        "redirect_to": redirect_to,
        "exp":         datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_state(state: str) -> dict:
    try:
        return pyjwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state parameter")


def _callback_url(provider: str) -> str:
    return f"{_BACKEND_URL}/api/v1/auth/oauth/{provider}/callback"


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/{provider}/authorize")
async def authorize(provider: str, redirect_to: Optional[str] = None):
    """Return the provider authorization URL.

    The frontend should redirect the user to this URL.
    The state parameter embeds the redirect_to destination so the callback
    can send the user back to the right place.
    """
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown OAuth provider: '{provider}'")

    cfg = _PROVIDERS[provider]
    client_id = os.environ.get(cfg["client_id_env"])
    if not client_id:
        raise HTTPException(
            status_code=503,
            detail=f"{provider} OAuth is not configured on this server",
        )

    dest = redirect_to or f"{_FRONTEND_URL}/auth/callback"
    state = _make_state(dest)

    params: dict[str, str] = {
        "client_id":    client_id,
        "redirect_uri": _callback_url(provider),
        "scope":        cfg["scope"],
        "state":        state,
        "response_type": "code",
    }
    if provider == "google":
        params["access_type"] = "online"
        params["prompt"] = "select_account"

    auth_url = f"{cfg['auth_url']}?{urlencode(params)}"
    return {"auth_url": auth_url, "provider": provider}


@router.get("/{provider}/callback")
async def callback(
    provider:   str,
    code:       Optional[str] = None,
    state:      Optional[str] = None,
    error:      Optional[str] = None,
    conn=Depends(get_conn),
):
    """Handle the provider redirect back to our server.

    Exchanges the code for an access token, fetches the user profile,
    upserts the user in the database, issues a JWT, and redirects to the
    frontend with ?token=<jwt>&email=...&name=...
    """
    # Provider declined (user cancelled, etc.)
    if error:
        return RedirectResponse(f"{_FRONTEND_URL}/login?error={error}")

    if provider not in _PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown OAuth provider: '{provider}'")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state in OAuth callback")

    state_data   = _decode_state(state)
    redirect_to  = state_data.get("redirect_to", f"{_FRONTEND_URL}/auth/callback")

    cfg           = _PROVIDERS[provider]
    client_id     = os.environ.get(cfg["client_id_env"])
    client_secret = os.environ.get(cfg["client_secret_env"])
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail=f"{provider} OAuth is not configured on this server",
        )

    async with httpx.AsyncClient() as http:
        # Exchange code for access token
        token_resp = await http.post(
            cfg["token_url"],
            data={
                "client_id":     client_id,
                "client_secret": client_secret,
                "code":          code,
                "redirect_uri":  _callback_url(provider),
                "grant_type":    "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="OAuth provider did not return an access token")

        # Fetch user profile
        profile_resp = await http.get(
            cfg["profile_url"],
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        # Extract normalised fields per provider
        if provider == "github":
            provider_id = str(profile["id"])
            name        = profile.get("name") or profile.get("login")
            avatar_url  = profile.get("avatar_url")
            email       = profile.get("email")
            # GitHub may withhold email from profile; fetch from emails endpoint
            if not email:
                emails_resp = await http.get(
                    cfg["emails_url"],
                    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                )
                emails = emails_resp.json() if emails_resp.is_success else []
                primary = next(
                    (e for e in emails if e.get("primary") and e.get("verified")), None
                )
                email = primary["email"] if primary else None

        elif provider == "google":
            provider_id = profile.get("id") or profile.get("sub")
            name        = profile.get("name")
            email       = profile.get("email")
            avatar_url  = profile.get("picture")

        elif provider == "linkedin":
            provider_id = profile.get("sub")
            name        = profile.get("name")
            email       = profile.get("email")
            avatar_url  = profile.get("picture")

        else:
            raise HTTPException(status_code=400, detail=f"Unhandled provider: {provider}")

    if not email:
        return RedirectResponse(f"{_FRONTEND_URL}/login?error=no_email")

    # Upsert user: look up by (provider, provider_id) first, then by email
    user = await conn.fetchrow(
        "SELECT id, email, display_name FROM app_user WHERE oauth_provider=$1 AND oauth_provider_id=$2",
        provider, str(provider_id),
    )

    if user is None:
        # Check if email already exists from a different provider or password signup
        user = await conn.fetchrow(
            "SELECT id, email, display_name FROM app_user WHERE email=$1",
            email,
        )
        if user:
            # Link the OAuth identity to the existing account
            await conn.execute(
                """UPDATE app_user
                   SET oauth_provider=$1, oauth_provider_id=$2, avatar_url=$3
                   WHERE id=$4""",
                provider, str(provider_id), avatar_url, user["id"],
            )
        else:
            # Brand new user - no password stored
            user = await conn.fetchrow(
                """INSERT INTO app_user
                     (email, display_name, password_hash, oauth_provider, oauth_provider_id, avatar_url)
                   VALUES ($1, $2, NULL, $3, $4, $5)
                   RETURNING id, email, display_name""",
                email, name, provider, str(provider_id), avatar_url,
            )

    # Issue JWT (30-day expiry for OAuth sessions)
    expire = datetime.now(timezone.utc) + timedelta(days=_OAUTH_TOKEN_EXPIRE_DAYS)
    token  = pyjwt.encode(
        {"sub": str(user["id"]), "email": user["email"], "exp": expire, "iat": datetime.now(timezone.utc)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    qs = urlencode({"token": token, "email": email, "name": name or ""})
    return RedirectResponse(f"{redirect_to}?{qs}")
