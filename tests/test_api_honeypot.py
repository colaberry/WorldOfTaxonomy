"""Tests for honeypot routes and /.well-known/security.txt."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from world_of_taxonomy.api.app import create_app


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def client(db_pool, monkeypatch):
    monkeypatch.delenv("METRICS_TOKEN", raising=False)
    app = create_app()
    app.state.pool = db_pool
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def test_security_txt_served(client):
    async def _test():
        resp = await client.get("/.well-known/security.txt")
        assert resp.status_code == 200
        body = resp.text
        assert "Contact:" in body
        assert "Expires:" in body
        await client.aclose()

    _run(_test())


def test_honeypot_returns_404(client):
    async def _test():
        for path in ("/wp-admin", "/.env", "/phpmyadmin", "/.git/config"):
            resp = await client.get(path)
            assert resp.status_code == 404, path
        await client.aclose()

    _run(_test())


def test_honeypot_increments_counter(client):
    from world_of_taxonomy.api.honeypot import HONEYPOT_HITS

    async def _test():
        before = HONEYPOT_HITS.labels(path="/wp-admin")._value.get()
        await client.get("/wp-admin")
        after = HONEYPOT_HITS.labels(path="/wp-admin")._value.get()
        assert after == before + 1
        await client.aclose()

    _run(_test())
