"""Tests for world_of_taxonomy.api.rate_guard.

Covers the two abuse-protection layers:

  - check_per_ip_rate: in-process per-IP cap. Allows the first N
    requests, raises 429 on the (N+1)-th. Different IPs get separate
    buckets. Window aging (eviction of old hits) is tested with
    monkey-patching time.monotonic so we do not have to wait
    real time.

  - check_email_send_budget: DB-backed global cap. Reads
    `email_send_log` for the trailing hour and raises 503 when the
    cap is reached. Cap is configurable via the EMAIL_SEND_BUDGET_PER_HOUR
    env var or an explicit `max_per_hour=` arg.

  - record_email_send: appends a row; failures are swallowed.
"""

import asyncio
import os

import pytest
from fastapi import HTTPException

from world_of_taxonomy.api.rate_guard import (
    _client_ip,
    _hash_email,
    _reset_for_tests,
    check_email_send_budget,
    check_per_ip_rate,
    record_email_send,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ----- per-IP rate limit -----------------------------------------------------


class _StubRequest:
    """Minimal Request stand-in. Only the headers + client.host are
    read by `_client_ip`; everything else can be omitted."""

    class _Client:
        def __init__(self, host):
            self.host = host

    def __init__(self, ip="1.2.3.4", forwarded_for=None):
        self.client = self._Client(ip) if ip else None
        self.headers = {}
        if forwarded_for is not None:
            self.headers["x-forwarded-for"] = forwarded_for


@pytest.mark.cli
class TestPerIPRateLimit:
    def setup_method(self):
        _reset_for_tests()

    def test_first_n_pass(self):
        req = _StubRequest()
        for _ in range(5):
            check_per_ip_rate("e", req, max_per_window=5)

    def test_n_plus_one_raises_429(self):
        req = _StubRequest()
        for _ in range(5):
            check_per_ip_rate("e", req, max_per_window=5)
        with pytest.raises(HTTPException) as exc:
            check_per_ip_rate("e", req, max_per_window=5)
        assert exc.value.status_code == 429
        body = exc.value.detail
        assert body["error"] == "rate_limit_exceeded"
        assert body["scope"] == "per_ip:e"
        assert "retry_after_seconds" in body
        assert "Retry-After" in exc.value.headers

    def test_distinct_ips_have_distinct_buckets(self):
        a = _StubRequest(ip="1.1.1.1")
        b = _StubRequest(ip="2.2.2.2")
        for _ in range(3):
            check_per_ip_rate("e", a, max_per_window=3)
        # IP B is fresh; should pass.
        check_per_ip_rate("e", b, max_per_window=3)

    def test_distinct_endpoints_have_distinct_buckets(self):
        req = _StubRequest()
        for _ in range(3):
            check_per_ip_rate("signup", req, max_per_window=3)
        # Same IP, different endpoint -> fresh bucket.
        check_per_ip_rate("magic_callback", req, max_per_window=3)

    def test_x_forwarded_for_takes_priority(self):
        a = _StubRequest(ip="10.0.0.1", forwarded_for="203.0.113.5")
        b = _StubRequest(ip="10.0.0.2", forwarded_for="203.0.113.5")
        # Both requests come from different sockets but the same
        # original client per X-Forwarded-For -> should share a bucket.
        for _ in range(3):
            check_per_ip_rate("e", a, max_per_window=3)
        with pytest.raises(HTTPException):
            check_per_ip_rate("e", b, max_per_window=3)

    def test_zero_limit_disables(self):
        req = _StubRequest()
        for _ in range(100):
            check_per_ip_rate("e", req, max_per_window=0)

    def test_aging_clears_bucket(self, monkeypatch):
        import world_of_taxonomy.api.rate_guard as rg
        t = [1000.0]
        monkeypatch.setattr(rg.time, "monotonic", lambda: t[0])

        req = _StubRequest()
        for _ in range(5):
            check_per_ip_rate("e", req, max_per_window=5, window_seconds=60)
        # Advance clock past the window - oldest hits should evict.
        t[0] += 61
        # Now the bucket should be effectively empty; 5 more allowed.
        for _ in range(5):
            check_per_ip_rate("e", req, max_per_window=5, window_seconds=60)


# ----- email-send budget guard (DB-backed) -----------------------------------


class TestEmailSendBudget:
    def test_under_cap_passes(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                # Start clean.
                await conn.execute("DELETE FROM email_send_log")
                # Two recent sends, well under the default cap.
                await conn.execute(
                    "INSERT INTO email_send_log (email_hash) VALUES ('a'), ('b')"
                )
                await check_email_send_budget(conn, max_per_hour=200)
        _run(go())

    def test_at_cap_raises_503(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                # Cap=3; insert 3 sends. The check is `>=` so 3 trips.
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash)
                       SELECT 'h-' || g FROM generate_series(1, 3) AS g"""
                )
                with pytest.raises(HTTPException) as exc:
                    await check_email_send_budget(conn, max_per_hour=3)
                assert exc.value.status_code == 503
                assert exc.value.detail["error"] == "email_budget_exhausted"
        _run(go())

    def test_old_rows_do_not_count(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                # 5 rows from 2 hours ago, none in the last hour.
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash, sent_at)
                       SELECT 'old-' || g, NOW() - INTERVAL '2 hours'
                       FROM generate_series(1, 5) AS g"""
                )
                # Cap=3 should not trip because the rolling-hour count is 0.
                await check_email_send_budget(conn, max_per_hour=3)
        _run(go())

    def test_cap_zero_disables(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                await conn.execute(
                    """INSERT INTO email_send_log (email_hash)
                       SELECT 'h-' || g FROM generate_series(1, 50) AS g"""
                )
                # 50 sends but cap=0 should disable the guard entirely.
                await check_email_send_budget(conn, max_per_hour=0)
        _run(go())

    def test_env_var_resolves_default(self, db_pool, monkeypatch):
        monkeypatch.setenv("EMAIL_SEND_BUDGET_PER_HOUR", "2")
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                await conn.execute(
                    "INSERT INTO email_send_log (email_hash) VALUES ('a'), ('b')"
                )
                # No explicit cap; resolver reads the env (=2). Trips.
                with pytest.raises(HTTPException) as exc:
                    await check_email_send_budget(conn)
                assert exc.value.status_code == 503
        _run(go())


class TestRecordEmailSend:
    def test_writes_one_row(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                await record_email_send(
                    conn, email="alice@example.com",
                    ip_address="10.0.0.1", purpose="magic_link",
                )
                row = await conn.fetchrow(
                    "SELECT email_hash, ip_address, purpose FROM email_send_log"
                )
                assert row["email_hash"] == _hash_email("alice@example.com")
                assert row["ip_address"] == "10.0.0.1"
                assert row["purpose"] == "magic_link"
        _run(go())

    def test_unknown_purpose_normalizes_to_other(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM email_send_log")
                await record_email_send(
                    conn, email="x@y.com", ip_address=None, purpose="not_a_thing",
                )
                row = await conn.fetchval(
                    "SELECT purpose FROM email_send_log"
                )
                assert row == "other"
        _run(go())


@pytest.mark.cli
def test_client_ip_handles_missing_socket():
    class NoClient:
        client = None
        headers = {}
    assert _client_ip(NoClient()) == "unknown"
