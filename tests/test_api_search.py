"""Tests for /api/v1/search endpoint.

TDD RED phase: these tests define the contract for the search router.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxonomy.api.app import create_app


@pytest.fixture
def app(db_pool):
    application = create_app()
    application.state.pool = db_pool
    return application


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


def test_search(client):
    async def _test():
        resp = await client.get("/api/v1/search", params={"q": "physician"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    _run(_test())


def test_search_with_system_filter(client):
    async def _test():
        resp = await client.get("/api/v1/search", params={"q": "health", "system": "naics_2022"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data:
            assert item["system_id"] == "naics_2022"
    _run(_test())


def test_search_with_limit(client):
    async def _test():
        resp = await client.get("/api/v1/search", params={"q": "farming", "limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 3
    _run(_test())


def test_search_no_results(client):
    async def _test():
        resp = await client.get("/api/v1/search", params={"q": "xyznonexistent"})
        assert resp.status_code == 200
        data = resp.json()
        assert data == []
    _run(_test())


def test_search_missing_query(client):
    async def _test():
        resp = await client.get("/api/v1/search")
        assert resp.status_code == 422  # Validation error
    _run(_test())


def test_search_with_multiple_system_ids(client):
    """Multi-system filter: results come from any of the selected systems."""
    async def _test():
        # Baseline: searching "agric" without filter hits all 3 seeded systems
        baseline = await client.get("/api/v1/search", params={"q": "agric"})
        baseline_systems = {item["system_id"] for item in baseline.json()}
        assert "sic_1987" in baseline_systems

        resp = await client.get(
            "/api/v1/search",
            params=[("q", "agric"), ("system_id", "naics_2022"), ("system_id", "isic_rev4")],
        )
        assert resp.status_code == 200
        data = resp.json()
        seen_systems = {item["system_id"] for item in data}
        assert seen_systems <= {"naics_2022", "isic_rev4"}
        assert "sic_1987" not in seen_systems
        assert len(seen_systems) == 2
    _run(_test())


def test_search_with_multiple_systems_alias(client):
    async def _test():
        resp = await client.get(
            "/api/v1/search",
            params=[("q", "agric"), ("system", "naics_2022"), ("system", "isic_rev4")],
        )
        assert resp.status_code == 200
        data = resp.json()
        seen_systems = {item["system_id"] for item in data}
        assert seen_systems <= {"naics_2022", "isic_rev4"}
        assert "sic_1987" not in seen_systems
    _run(_test())


class TestSearchPerIPRateLimit:
    """The /search route applies a per-IP rate guard (200/hour). The
    cap is high enough to be a no-op for any interactive use; the test
    drops the cap via direct call to verify the guard wires correctly.
    """

    def setup_method(self):
        from world_of_taxonomy.api.rate_guard import _reset_for_tests
        _reset_for_tests()

    def test_search_rate_limit_fires_when_cap_exceeded(self, monkeypatch, client):
        """Lower the search cap to 3 via monkeypatch on check_per_ip_rate
        so we don't have to issue 200 real queries to prove the guard
        is wired."""
        from world_of_taxonomy.api.routers import search as search_mod
        from world_of_taxonomy.api.rate_guard import check_per_ip_rate

        def _capped(endpoint_name, request, max_per_window=200, **kw):
            if endpoint_name == "search":
                max_per_window = 3
            return check_per_ip_rate(endpoint_name, request, max_per_window=max_per_window, **kw)

        monkeypatch.setattr(search_mod, "check_per_ip_rate", _capped)

        async def _test():
            for i in range(3):
                resp = await client.get("/api/v1/search", params={"q": "health"})
                assert resp.status_code == 200, (i, resp.text)
            resp = await client.get("/api/v1/search", params={"q": "health"})
            assert resp.status_code == 429
            body = resp.json()["detail"]
            assert body["error"] == "rate_limit_exceeded"
            assert body["scope"] == "per_ip:search"
            assert resp.headers.get("retry-after") is not None
        _run(_test())
