"""Tests for the four ops-hardening adds:

  (a) Prometheus counter on rate-guard 429s + 503s.
  (b) cleanup_email_send_log script deletes only old rows.
  (c) Anti-CSRF on cookie-gated /developers/keys POST and DELETE.
  (d) audit_abandoned_keys script identifies + optionally revokes
      idle keys.

These are unit-flavoured: items (a) and (c) drive the route functions
directly with stub Requests; items (b) and (d) hit a real test pool.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys

import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ----- (a) RATE_GUARD_FIRED counter ---------------------------------------


class TestRateGuardCounter:
    def setup_method(self):
        from world_of_taxonomy.api.rate_guard import _reset_for_tests
        _reset_for_tests()

    def test_per_ip_429_increments_counter(self):
        from fastapi import HTTPException
        from world_of_taxonomy.api.rate_guard import check_per_ip_rate
        from world_of_taxonomy.api.metrics import RATE_GUARD_FIRED

        # prometheus_client exposes a Value primitive on each labelled
        # child; .get() returns the current float.
        child = RATE_GUARD_FIRED.labels(endpoint="t_unit")
        before = child._value.get()  # type: ignore[attr-defined]

        class _Client:
            host = "1.2.3.4"

        class _Req:
            client = _Client()
            headers = {}

        # First call passes (cap=1, first hit).
        check_per_ip_rate("t_unit", _Req(), max_per_window=1)
        # Second call trips and increments the counter.
        with pytest.raises(HTTPException) as exc:
            check_per_ip_rate("t_unit", _Req(), max_per_window=1)
        assert exc.value.status_code == 429

        after = child._value.get()  # type: ignore[attr-defined]
        assert after == before + 1


# ----- (b) cleanup_email_send_log -----------------------------------------


class TestCleanupEmailSendLog:
    def test_dry_run_reports_count_and_does_not_delete(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash, sent_at)
                       SELECT 'old-' || g, NOW() - INTERVAL '14 days'
                       FROM generate_series(1, 2) AS g"""
                )
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash, sent_at)
                       VALUES ('fresh-1', NOW() - INTERVAL '1 hour')"""
                )

                mod = importlib.import_module("scripts.cleanup_email_send_log")
                importlib.reload(mod)
                count = await mod.cleanup(days=7, dry_run=True, conn=conn)
                assert count == 2

                total = await conn.fetchval("SELECT count(*) FROM email_send_log")
                assert total == 3, "dry-run must not delete"
        _run(go())

    def test_real_run_deletes_only_old(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash, sent_at)
                       SELECT 'old-' || g, NOW() - INTERVAL '10 days'
                       FROM generate_series(1, 3) AS g"""
                )
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash, sent_at)
                       VALUES ('fresh-1', NOW() - INTERVAL '1 hour')"""
                )

                mod = importlib.import_module("scripts.cleanup_email_send_log")
                importlib.reload(mod)
                deleted = await mod.cleanup(days=7, dry_run=False, conn=conn)
                assert deleted == 3

                remaining = await conn.fetch(
                    "SELECT email_hash FROM email_send_log ORDER BY email_hash"
                )
                assert [r["email_hash"] for r in remaining] == ["fresh-1"]
        _run(go())


# ----- (c) Anti-CSRF on /developers/keys POST + DELETE --------------------


class TestCsrfDoubleSubmit:
    """Wiring tests; the rate-guard chain is stubbed out so the route
    reaches the CSRF check directly."""

    def setup_method(self):
        from world_of_taxonomy.api.rate_guard import _reset_for_tests
        _reset_for_tests()

    def _stub_request(self, *, csrf_cookie=None, csrf_header=None):
        class _Client:
            host = "1.2.3.4"

        class _Req:
            client = _Client()
            cookies = {}
            headers = {}

        req = _Req()
        if csrf_cookie is not None:
            req.cookies["wot_csrf"] = csrf_cookie
        if csrf_header is not None:
            req.headers["x-csrf-token"] = csrf_header
        return req

    def test_create_key_without_csrf_returns_403(self, monkeypatch):
        from fastapi import HTTPException
        from world_of_taxonomy.api.routers import developers as dev_mod

        # Bypass rate guard so the test reaches the CSRF check.
        monkeypatch.setattr(dev_mod, "check_per_ip_rate", lambda *a, **kw: None)

        body = dev_mod.CreateKeyRequest(name="ci", scopes=["wot:read"])

        async def go():
            with pytest.raises(HTTPException) as exc:
                await dev_mod.create_key(
                    body,
                    self._stub_request(),  # no csrf cookie/header
                    user={"id": "00000000-0000-0000-0000-000000000000"},
                    conn=None,
                )
            assert exc.value.status_code == 403
            assert exc.value.detail["error"] == "csrf_token_mismatch"
        _run(go())

    def test_create_key_with_mismatched_csrf_returns_403(self, monkeypatch):
        from fastapi import HTTPException
        from world_of_taxonomy.api.routers import developers as dev_mod
        monkeypatch.setattr(dev_mod, "check_per_ip_rate", lambda *a, **kw: None)

        body = dev_mod.CreateKeyRequest(name="ci", scopes=["wot:read"])

        async def go():
            with pytest.raises(HTTPException) as exc:
                await dev_mod.create_key(
                    body,
                    self._stub_request(csrf_cookie="aaaa", csrf_header="bbbb"),
                    user={"id": "00000000-0000-0000-0000-000000000000"},
                    conn=None,
                )
            assert exc.value.status_code == 403
        _run(go())

    def test_revoke_key_without_csrf_returns_403(self, monkeypatch):
        from fastapi import HTTPException
        from world_of_taxonomy.api.routers import developers as dev_mod

        async def go():
            with pytest.raises(HTTPException) as exc:
                await dev_mod.revoke_key(
                    "00000000-0000-0000-0000-000000000000",
                    self._stub_request(),
                    user={"id": "00000000-0000-0000-0000-000000000000"},
                    conn=None,
                )
            assert exc.value.status_code == 403
        _run(go())


# ----- (d) audit_abandoned_keys -------------------------------------------


class TestAuditAbandonedKeys:
    async def _make_user(self, conn):
        org_id = await conn.fetchval(
            """INSERT INTO org (name, domain, kind)
               VALUES ('audit-corp', 'audit-corp.com', 'corporate')
               RETURNING id"""
        )
        user_id = await conn.fetchval(
            """INSERT INTO app_user (email, org_id, role)
               VALUES ('audit@audit-corp.com', $1, 'admin')
               RETURNING id""",
            org_id,
        )
        return user_id

    def test_idle_keys_listed_not_revoked_by_default(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM api_key")
                await conn.execute("DELETE FROM app_user WHERE email LIKE 'audit@%'")
                await conn.execute("DELETE FROM org WHERE domain = 'audit-corp.com'")
                user_id = await self._make_user(conn)
                # Old key (last_used 200 days ago)
                await conn.execute(
                    """INSERT INTO api_key
                          (user_id, key_hash, key_prefix, scopes, name, last_used_at)
                       VALUES ($1, 'h1', 'pfx00001', ARRAY['wot:read'],
                               'old', NOW() - INTERVAL '200 days')""",
                    user_id,
                )
                # Fresh key (used today)
                await conn.execute(
                    """INSERT INTO api_key
                          (user_id, key_hash, key_prefix, scopes, name, last_used_at)
                       VALUES ($1, 'h2', 'pfx00002', ARRAY['wot:read'],
                               'fresh', NOW())""",
                    user_id,
                )

                mod = importlib.import_module("scripts.audit_abandoned_keys")
                importlib.reload(mod)
                count = await mod.audit(days=180, revoke=False, conn=conn)
            assert count == 1

            async with db_pool.acquire() as conn:
                # Default mode does not revoke.
                live = await conn.fetchval(
                    "SELECT count(*) FROM api_key WHERE revoked_at IS NULL"
                )
                assert live == 2
        _run(go())

    def test_revoke_mode_marks_idle_keys_revoked(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM api_key")
                await conn.execute("DELETE FROM app_user WHERE email LIKE 'audit@%'")
                await conn.execute("DELETE FROM org WHERE domain = 'audit-corp.com'")
                user_id = await self._make_user(conn)
                await conn.execute(
                    """INSERT INTO api_key
                          (user_id, key_hash, key_prefix, scopes, name, last_used_at)
                       VALUES ($1, 'h1', 'pfx00001', ARRAY['wot:read'],
                               'old', NOW() - INTERVAL '200 days')""",
                    user_id,
                )

                mod = importlib.import_module("scripts.audit_abandoned_keys")
                importlib.reload(mod)
                count = await mod.audit(days=180, revoke=True, conn=conn)
                assert count == 1

                row = await conn.fetchrow(
                    "SELECT revoked_at, revoked_reason FROM api_key"
                )
                assert row["revoked_at"] is not None
                assert row["revoked_reason"] == "abandoned_180d"
        _run(go())

    def test_never_used_key_inside_grace_window_not_flagged(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM api_key")
                await conn.execute("DELETE FROM app_user WHERE email LIKE 'audit@%'")
                await conn.execute("DELETE FROM org WHERE domain = 'audit-corp.com'")
                user_id = await self._make_user(conn)
                # Never-used key created yesterday should NOT be flagged
                # at 180-day threshold.
                await conn.execute(
                    """INSERT INTO api_key
                          (user_id, key_hash, key_prefix, scopes, name)
                       VALUES ($1, 'h1', 'pfx00001', ARRAY['wot:read'], 'newish')""",
                    user_id,
                )

                mod = importlib.import_module("scripts.audit_abandoned_keys")
                importlib.reload(mod)
                count = await mod.audit(days=180, revoke=False, conn=conn)
            assert count == 0
        _run(go())
