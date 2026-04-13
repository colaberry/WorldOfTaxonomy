"""Tests for OAuth 2.0 social login - GitHub, Google, LinkedIn.

TDD RED phase: defines the contract for OAuth authorize + callback endpoints.
Uses the test_wot schema (never touches production data).
"""

import asyncio
import os
import pytest
import jwt
from unittest.mock import patch, AsyncMock, MagicMock
from urllib.parse import urlparse, parse_qs
from httpx import AsyncClient, ASGITransport

from world_of_taxanomy.api.app import create_app
from world_of_taxanomy.api.deps import JWT_SECRET, JWT_ALGORITHM


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def app(db_pool):
    application = create_app()
    application.state.pool = db_pool
    return application


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _valid_state(redirect_to="http://localhost:3000/auth/callback"):
    """Create a valid signed state JWT for use in callback tests."""
    from world_of_taxanomy.api.routers.oauth import _make_state
    return _make_state(redirect_to)


# ── Authorize endpoint ──────────────────────────────────────────────────────


class TestOAuthAuthorize:
    def test_github_authorize_returns_auth_url(self, client):
        """GET /authorize for github returns a URL pointing to github.com."""
        async def _test():
            with patch.dict("os.environ", {"GITHUB_CLIENT_ID": "gh_test_id"}):
                resp = await client.get("/api/v1/auth/oauth/github/authorize")
            assert resp.status_code == 200
            data = resp.json()
            assert "auth_url" in data
            assert "github.com/login/oauth/authorize" in data["auth_url"]
            assert "client_id=gh_test_id" in data["auth_url"]
            assert "state=" in data["auth_url"]
        _run(_test())

    def test_google_authorize_returns_auth_url(self, client):
        """GET /authorize for google returns a URL pointing to accounts.google.com."""
        async def _test():
            with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "goog_test_id"}):
                resp = await client.get("/api/v1/auth/oauth/google/authorize")
            assert resp.status_code == 200
            data = resp.json()
            assert "auth_url" in data
            assert "accounts.google.com" in data["auth_url"]
            assert "client_id=goog_test_id" in data["auth_url"]
        _run(_test())

    def test_linkedin_authorize_returns_auth_url(self, client):
        """GET /authorize for linkedin returns a URL pointing to linkedin.com."""
        async def _test():
            with patch.dict("os.environ", {"LINKEDIN_CLIENT_ID": "li_test_id"}):
                resp = await client.get("/api/v1/auth/oauth/linkedin/authorize")
            assert resp.status_code == 200
            data = resp.json()
            assert "auth_url" in data
            assert "linkedin.com" in data["auth_url"]
        _run(_test())

    def test_unknown_provider_returns_400(self, client):
        """Unknown provider name returns 400."""
        async def _test():
            resp = await client.get("/api/v1/auth/oauth/twitter/authorize")
            assert resp.status_code == 400
        _run(_test())

    def test_unconfigured_provider_returns_503(self, client):
        """Provider with no client_id env var configured returns 503."""
        async def _test():
            saved = os.environ.pop("GITHUB_CLIENT_ID", None)
            try:
                resp = await client.get("/api/v1/auth/oauth/github/authorize")
                assert resp.status_code == 503
            finally:
                if saved is not None:
                    os.environ["GITHUB_CLIENT_ID"] = saved
        _run(_test())

    def test_authorize_returns_provider_name(self, client):
        """Response includes provider field matching the path param."""
        async def _test():
            with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "goog_id"}):
                resp = await client.get("/api/v1/auth/oauth/google/authorize")
            assert resp.json()["provider"] == "google"
        _run(_test())

    def test_auth_url_includes_redirect_uri(self, client):
        """The provider auth URL includes our backend callback as redirect_uri."""
        async def _test():
            with patch.dict("os.environ", {"GITHUB_CLIENT_ID": "gh_id"}):
                resp = await client.get("/api/v1/auth/oauth/github/authorize")
            assert "redirect_uri=" in resp.json()["auth_url"]
        _run(_test())


# ── Callback endpoint ──────────────────────────────────────────────────────


class TestOAuthCallback:
    def test_unknown_provider_returns_400(self, client):
        """Callback for unknown provider returns 400."""
        async def _test():
            state = _valid_state()
            resp = await client.get(
                f"/api/v1/auth/oauth/foobar/callback?code=abc&state={state}"
            )
            assert resp.status_code == 400
        _run(_test())

    def test_missing_code_returns_400(self, client):
        """Callback without code param returns 400."""
        async def _test():
            state = _valid_state()
            resp = await client.get(
                f"/api/v1/auth/oauth/github/callback?state={state}"
            )
            assert resp.status_code == 400
        _run(_test())

    def test_invalid_state_returns_400(self, client):
        """Callback with tampered/expired state returns 400."""
        async def _test():
            resp = await client.get(
                "/api/v1/auth/oauth/github/callback?code=abc&state=not_a_valid_jwt"
            )
            assert resp.status_code == 400
        _run(_test())

    def test_error_param_redirects_to_login(self, client):
        """When provider sends error (e.g. user cancelled), redirects to /login."""
        async def _test():
            resp = await client.get(
                "/api/v1/auth/oauth/github/callback?error=access_denied",
                follow_redirects=False,
            )
            assert resp.status_code in (302, 307)
            assert "login" in resp.headers["location"]
        _run(_test())

    def _mock_github_http(self, profile: dict):
        """Return a mock httpx.AsyncClient that simulates GitHub OAuth responses."""
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "gh_test_token"}
        mock_token_resp.raise_for_status = MagicMock()

        mock_profile_resp = MagicMock()
        mock_profile_resp.json.return_value = profile
        mock_profile_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_token_resp)
        mock_http.get = AsyncMock(return_value=mock_profile_resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        return mock_http

    def test_github_callback_creates_new_user_and_redirects(self, client, db_pool):
        """Successful GitHub callback creates user in DB and redirects with JWT."""
        async def _test():
            state = _valid_state()
            profile = {
                "id": 12345,
                "login": "octocat",
                "name": "The Octocat",
                "email": "octocat@github.com",
                "avatar_url": "https://avatars.githubusercontent.com/octocat",
            }
            mock_http = self._mock_github_http(profile)

            with patch.dict("os.environ", {
                "GITHUB_CLIENT_ID": "gh_id",
                "GITHUB_CLIENT_SECRET": "gh_secret",
            }):
                with patch("world_of_taxanomy.api.routers.oauth.httpx.AsyncClient") as cls:
                    cls.return_value = mock_http
                    resp = await client.get(
                        f"/api/v1/auth/oauth/github/callback?code=testcode&state={state}",
                        follow_redirects=False,
                    )

            assert resp.status_code in (302, 307)
            assert "token=" in resp.headers["location"]

            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT email, oauth_provider, oauth_provider_id FROM app_user WHERE email=$1",
                    "octocat@github.com",
                )
            assert row is not None
            assert row["oauth_provider"] == "github"
            assert row["oauth_provider_id"] == "12345"
        _run(_test())

    def test_github_callback_existing_email_no_duplicate(self, client, db_pool):
        """GitHub callback with already-registered email reuses existing user."""
        async def _test():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO app_user (email, password_hash, display_name)
                       VALUES ($1, NULL, $2)""",
                    "preexist@example.com", "Pre Existing",
                )

            state = _valid_state()
            profile = {
                "id": 55555,
                "login": "preexist",
                "name": "Pre Existing",
                "email": "preexist@example.com",
                "avatar_url": None,
            }
            mock_http = self._mock_github_http(profile)

            with patch.dict("os.environ", {
                "GITHUB_CLIENT_ID": "gh_id",
                "GITHUB_CLIENT_SECRET": "gh_secret",
            }):
                with patch("world_of_taxanomy.api.routers.oauth.httpx.AsyncClient") as cls:
                    cls.return_value = mock_http
                    await client.get(
                        f"/api/v1/auth/oauth/github/callback?code=testcode&state={state}",
                        follow_redirects=False,
                    )

            async with db_pool.acquire() as conn:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM app_user WHERE email=$1",
                    "preexist@example.com",
                )
            assert count == 1
        _run(_test())

    def test_callback_token_is_valid_jwt_with_sub_and_email(self, client, db_pool):
        """The token in the redirect URL decodes to a valid JWT with sub + email."""
        async def _test():
            state = _valid_state()
            profile = {
                "id": 99999,
                "login": "jwtcheck",
                "name": "JWT Check",
                "email": "jwtcheck@example.com",
                "avatar_url": None,
            }
            mock_http = self._mock_github_http(profile)

            with patch.dict("os.environ", {
                "GITHUB_CLIENT_ID": "gh_id",
                "GITHUB_CLIENT_SECRET": "gh_secret",
            }):
                with patch("world_of_taxanomy.api.routers.oauth.httpx.AsyncClient") as cls:
                    cls.return_value = mock_http
                    resp = await client.get(
                        f"/api/v1/auth/oauth/github/callback?code=testcode&state={state}",
                        follow_redirects=False,
                    )

            location = resp.headers["location"]
            params = parse_qs(urlparse(location).query)
            token = params["token"][0]
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            assert "sub" in decoded
            assert decoded["email"] == "jwtcheck@example.com"
        _run(_test())

    def test_oauth_user_has_null_password_hash(self, client, db_pool):
        """Users created via OAuth have NULL password_hash - no password stored."""
        async def _test():
            state = _valid_state()
            profile = {
                "id": 77777,
                "login": "nopwduser",
                "name": "No Password",
                "email": "nopwd@example.com",
                "avatar_url": None,
            }
            mock_http = self._mock_github_http(profile)

            with patch.dict("os.environ", {
                "GITHUB_CLIENT_ID": "gh_id",
                "GITHUB_CLIENT_SECRET": "gh_secret",
            }):
                with patch("world_of_taxanomy.api.routers.oauth.httpx.AsyncClient") as cls:
                    cls.return_value = mock_http
                    await client.get(
                        f"/api/v1/auth/oauth/github/callback?code=testcode&state={state}",
                        follow_redirects=False,
                    )

            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT password_hash FROM app_user WHERE email=$1",
                    "nopwd@example.com",
                )
            assert row["password_hash"] is None
        _run(_test())


# ── Password login blocked for OAuth users ──────────────────────────────────


class TestPasswordLoginBlockedForOAuthUsers:
    def test_password_login_rejected_for_oauth_user(self, client, db_pool):
        """A user registered via OAuth cannot log in with a password."""
        async def _test():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO app_user
                         (email, password_hash, display_name, oauth_provider, oauth_provider_id)
                       VALUES ($1, NULL, $2, $3, $4)""",
                    "oauthonly@example.com", "OAuth Only", "github", "11111",
                )

            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "oauthonly@example.com", "password": "anything"},
            )
            assert resp.status_code == 401
            assert "social login" in resp.json()["detail"].lower()
        _run(_test())
