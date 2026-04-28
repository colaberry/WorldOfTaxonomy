"""Tests for require_tier dependency - the scope+tier gate used on
paid-only endpoints (bulk_export, classify).

Asserts the contract end-to-end via the bulk_export router so we
exercise the real dependency wiring, not a mock.
"""

import asyncio
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from httpx import AsyncClient, ASGITransport


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def app(db_pool):
    os.environ.setdefault("DATABASE_URL", os.environ["DATABASE_URL"])
    os.environ.setdefault("JWT_SECRET", "x" * 40)
    from world_of_taxonomy.api.app import create_app
    app = create_app()
    app.state.pool = db_pool
    return app


def _client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


async def _make_org_user_key(conn, *, tier: str, scopes):
    """Create an org with the given tier, a user inside it, and an
    api_key with the given scopes. Returns the raw key string."""
    org_id = await conn.fetchval(
        """INSERT INTO org (name, domain, kind, tier)
           VALUES ('acme', $1, 'corporate', $2) RETURNING id""",
        f"acme-{secrets.token_hex(4)}.com", tier,
    )
    user_id = await conn.fetchval(
        """INSERT INTO app_user (email, org_id, role)
           VALUES ($1, $2, 'admin') RETURNING id""",
        f"u-{secrets.token_hex(4)}@acme.com", org_id,
    )
    from world_of_taxonomy.auth.keys import issue_key
    minted = issue_key(scopes)
    await conn.execute(
        """INSERT INTO api_key (user_id, key_hash, key_prefix, scopes, name)
           VALUES ($1, $2, $3, $4, 'test')""",
        user_id, minted["key_hash"], minted["key_prefix"], list(scopes),
    )
    return minted["raw_key"]


class TestRequireTierContract:
    def test_anon_returns_401_with_helpful_headers(self, app):
        async def _test():
            async with _client(app) as c:
                resp = await c.get("/api/v1/export/systems.jsonl")
                assert resp.status_code == 401
                body = resp.json().get("detail", {})
                assert body.get("error") == "missing_api_key"
                assert resp.headers.get("www-authenticate", "").lower().startswith("apikey")
                assert 'rel="signup"' in resp.headers.get("link", "")
        _run(_test())

    def test_key_with_scope_but_free_tier_returns_403_tier_required(self, app, db_pool):
        async def _test():
            async with db_pool.acquire() as conn:
                raw = await _make_org_user_key(
                    conn, tier="free", scopes=["wot:export"],
                )
            async with _client(app) as c:
                resp = await c.get(
                    "/api/v1/export/systems.jsonl",
                    headers={"Authorization": f"Bearer {raw}"},
                )
                assert resp.status_code == 403
                body = resp.json().get("detail", {})
                assert body.get("error") == "tier_required"
                assert "pro" in body.get("required_tier", "")
                assert 'rel="upgrade"' in resp.headers.get("link", "")
        _run(_test())

    def test_key_without_scope_returns_403_scope_missing(self, app, db_pool):
        async def _test():
            async with db_pool.acquire() as conn:
                raw = await _make_org_user_key(
                    conn, tier="pro", scopes=["wot:read"],
                )
            async with _client(app) as c:
                resp = await c.get(
                    "/api/v1/export/systems.jsonl",
                    headers={"Authorization": f"Bearer {raw}"},
                )
                assert resp.status_code == 403
                body = resp.json().get("detail", {})
                assert body.get("error") == "scope_missing"
                assert body.get("required_scope") == "wot:export"
        _run(_test())

    def test_key_with_scope_and_pro_tier_returns_200(self, app, db_pool):
        async def _test():
            async with db_pool.acquire() as conn:
                raw = await _make_org_user_key(
                    conn, tier="pro", scopes=["wot:export"],
                )
            async with _client(app) as c:
                resp = await c.get(
                    "/api/v1/export/systems.jsonl",
                    headers={"Authorization": f"Bearer {raw}"},
                )
                assert resp.status_code == 200, resp.text
                # JSONL: first line should parse as a JSON object.
                first_line = resp.text.split("\n", 1)[0]
                assert first_line.startswith("{")
        _run(_test())

    def test_crosswalks_endpoint_requires_enterprise_tier_specifically(self, app, db_pool):
        async def _test():
            async with db_pool.acquire() as conn:
                pro_key = await _make_org_user_key(
                    conn, tier="pro", scopes=["wot:export"],
                )
            async with _client(app) as c:
                # pro tier denied on crosswalks (enterprise-only).
                resp = await c.get(
                    "/api/v1/export/crosswalks.jsonl",
                    headers={"Authorization": f"Bearer {pro_key}"},
                )
                assert resp.status_code == 403
                body = resp.json().get("detail", {})
                assert body.get("error") == "tier_required"
                assert body.get("required_tier") == "enterprise"
        _run(_test())

    def test_revoked_key_returns_401_invalid_api_key(self, app, db_pool):
        async def _test():
            async with db_pool.acquire() as conn:
                raw = await _make_org_user_key(
                    conn, tier="pro", scopes=["wot:export"],
                )
                # Revoke right after minting.
                await conn.execute(
                    """UPDATE api_key SET revoked_at = NOW(),
                                          revoked_reason = 'manual_test'"""
                )
            async with _client(app) as c:
                resp = await c.get(
                    "/api/v1/export/systems.jsonl",
                    headers={"Authorization": f"Bearer {raw}"},
                )
                assert resp.status_code == 401
                body = resp.json().get("detail", {})
                assert body.get("error") == "invalid_api_key"
        _run(_test())
