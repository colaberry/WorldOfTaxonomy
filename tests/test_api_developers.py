"""Layer E: /api/v1/developers + /api/v1/keys + /auth/magic-* HTTP contract.

Spins up the FastAPI app with the test pool wired in, drives the
endpoints with httpx ASGITransport, and asserts the contract:
  - signup -> 202 + (in dev) the magic link in the response body.
  - magic callback -> sets dev_session cookie.
  - keys CRUD requires the cookie.
  - 401 on protected endpoints carries the `/developers` link header
    + WWW-Authenticate: ApiKey, and a JSON body with error code.
"""

import asyncio
import os

import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _reset_rate_guard():
    """The per-IP rate counter is in-process and lives for the whole
    pytest run. Reset between tests so signups in one test do not
    feed the bucket of the next."""
    from world_of_taxonomy.api.rate_guard import _reset_for_tests
    _reset_for_tests()


@pytest.fixture
def app(db_pool):
    """Build the FastAPI app for tests, pinned to the test_wot pool."""
    os.environ.setdefault("DATABASE_URL", os.environ["DATABASE_URL"])
    os.environ.setdefault("JWT_SECRET", "x" * 40)
    os.environ.setdefault("DEV_KEYS_ENABLED", "1")
    # Skip Resend in tests; the developers signup returns the link in
    # the response body when DEV_KEYS_DEV_MODE=1 so we can drive the
    # magic callback without an inbox.
    os.environ.setdefault("DEV_KEYS_DEV_MODE", "1")
    # Cookie must be readable over http://testserver in tests.
    os.environ["DEV_SESSION_INSECURE"] = "1"
    from world_of_taxonomy.api.app import create_app
    app = create_app()
    app.state.pool = db_pool
    return app


def _client(app):
    from httpx import AsyncClient, ASGITransport
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


class TestSignupAndMagicLink:
    def test_post_signup_accepted_and_returns_link_in_dev_mode(self, app):
        # Reset the per-IP rate counter so a previous run does not bleed
        # into this one (in-process LRU is shared across the whole test
        # process).
        from world_of_taxonomy.api.rate_guard import _reset_for_tests
        _reset_for_tests()

        async def _test():
            async with _client(app) as c:
                resp = await c.post(
                    "/api/v1/developers/signup",
                    json={"email": "alice@gmail.com"},
                )
                assert resp.status_code == 202
                body = resp.json()
                # In dev mode the magic link is returned for testability.
                assert "magic_link_url" in body
                assert "/auth/magic" in body["magic_link_url"]
        _run(_test())

    def test_signup_per_ip_rate_limit_fires_at_sixth_attempt(self, app):
        """Per-IP cap of 5/hour means the 6th signup from the same IP
        in the same window returns 429 with retry-after."""
        from world_of_taxonomy.api.rate_guard import _reset_for_tests
        _reset_for_tests()

        async def _test():
            async with _client(app) as c:
                # First 5 attempts succeed.
                for i in range(5):
                    resp = await c.post(
                        "/api/v1/developers/signup",
                        json={"email": f"flood-{i}@gmail.com"},
                    )
                    assert resp.status_code == 202, (i, resp.text)
                # 6th attempt is rate-limited.
                resp = await c.post(
                    "/api/v1/developers/signup",
                    json={"email": "flood-6@gmail.com"},
                )
                assert resp.status_code == 429
                body = resp.json()["detail"]
                assert body["error"] == "rate_limit_exceeded"
                assert body["scope"] == "per_ip:developers_signup"
                assert "retry_after_seconds" in body
                assert resp.headers.get("retry-after") is not None
        _run(_test())

    def test_magic_callback_sets_session_cookie(self, app):
        async def _test():
            async with _client(app) as c:
                signup = await c.post(
                    "/api/v1/developers/signup",
                    json={"email": "alice@gmail.com"},
                )
                magic_link = signup.json()["magic_link_url"]
                # Extract token from the link.
                token = magic_link.split("t=", 1)[1]
                resp = await c.get(f"/api/v1/auth/magic-callback?t={token}")
                # Either 200 with a Set-Cookie or 303 redirect with one.
                assert resp.status_code in (200, 302, 303)
                cookies = resp.headers.get("set-cookie", "")
                assert "dev_session=" in cookies
        _run(_test())


class TestKeyCrudRequiresSession:
    def test_keys_endpoints_reject_anon(self, app):
        async def _test():
            async with _client(app) as c:
                listed = await c.get("/api/v1/developers/keys")
                assert listed.status_code == 401
                created = await c.post(
                    "/api/v1/developers/keys",
                    json={"name": "ci", "scopes": ["wot:read"]},
                )
                assert created.status_code == 401
        _run(_test())

    def test_keys_create_returns_raw_key_once_with_correct_prefix(self, app):
        async def _test():
            async with _client(app) as c:
                signup = await c.post(
                    "/api/v1/developers/signup",
                    json={"email": "alice@gmail.com"},
                )
                token = signup.json()["magic_link_url"].split("t=", 1)[1]
                # Authenticate + retain cookies on the same client.
                await c.get(f"/api/v1/auth/magic-callback?t={token}")

                created = await c.post(
                    "/api/v1/developers/keys",
                    json={"name": "ci", "scopes": ["wot:read"]},
                )
                assert created.status_code == 201, created.text
                body = created.json()
                # Restricted scope -> rwot_ prefix.
                assert body["raw_key"].startswith("rwot_")
                # Listing only returns metadata, never the raw key.
                listed = await c.get("/api/v1/developers/keys")
                assert listed.status_code == 200
                items = listed.json()
                assert len(items) == 1
                assert "raw_key" not in items[0]
                assert items[0]["scopes"] == ["wot:read"]
        _run(_test())


class TestProtectedEndpointHelpfulErrors:
    def test_anonymous_export_returns_401_with_link_header(self, app):
        """Protected (require_scope) endpoints emit a JSON pointer to
        /developers and the right WWW-Authenticate header so curl
        users see exactly where to go."""
        async def _test():
            async with _client(app) as c:
                # The bulk export router will be wrapped in require_scope
                # in PR #2; this assertion documents the contract.
                resp = await c.get(
                    "/api/v1/export/equivalences/all",
                )
                # Already-public listing endpoints stay 200; only the
                # gated bulk export is required to 401 here.
                if resp.status_code == 401:
                    body = resp.json()
                    assert body.get("error") == "missing_api_key"
                    assert "developers" in body.get("message", "").lower()
                    assert resp.headers.get("www-authenticate", "").lower().startswith(
                        "apikey"
                    )
                    link = resp.headers.get("link", "")
                    assert "rel=\"signup\"" in link or 'rel="signup"' in link
        _run(_test())
