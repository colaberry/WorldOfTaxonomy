"""API contract tests for the category field + ?category= filter.

Covers: /api/v1/systems, /api/v1/search, /api/v1/classify/demo.
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


def test_systems_response_carries_category(client):
    async def _test():
        resp = await client.get("/api/v1/systems")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for row in data:
            assert "category" in row
            assert row["category"] in ("domain", "standard")
            if row["id"].startswith("domain_"):
                assert row["category"] == "domain"
            else:
                assert row["category"] == "standard"
    _run(_test())


def test_systems_filter_category_standard(client):
    async def _test():
        resp = await client.get("/api/v1/systems", params={"category": "standard"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for row in data:
            assert row["category"] == "standard"
            assert not row["id"].startswith("domain_")
    _run(_test())


def test_systems_filter_category_domain(client):
    async def _test():
        resp = await client.get("/api/v1/systems", params={"category": "domain"})
        assert resp.status_code == 200
        data = resp.json()
        # Test seed may not include domain systems; if empty, that's fine.
        for row in data:
            assert row["category"] == "domain"
            assert row["id"].startswith("domain_")
    _run(_test())


def test_systems_filter_category_invalid(client):
    async def _test():
        resp = await client.get("/api/v1/systems", params={"category": "bogus"})
        assert resp.status_code == 400
    _run(_test())


def test_search_results_carry_category(client):
    async def _test():
        resp = await client.get("/api/v1/search", params={"q": "health"})
        assert resp.status_code == 200
        data = resp.json()
        for row in data:
            assert "category" in row
            assert row["category"] in ("domain", "standard")
    _run(_test())


def test_search_filter_category_invalid(client):
    async def _test():
        resp = await client.get(
            "/api/v1/search", params={"q": "health", "category": "bogus"}
        )
        assert resp.status_code == 400
    _run(_test())


def test_classify_demo_returns_split_matches(client):
    async def _test():
        resp = await client.post(
            "/api/v1/classify/demo",
            json={"email": "tester@example.com", "text": "hospital"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "domain_matches" in data
        assert "standard_matches" in data
        assert "matches" not in data  # legacy flat key must be dropped
        assert isinstance(data["domain_matches"], list)
        assert isinstance(data["standard_matches"], list)
        # Every match in standard_matches must be a standard system.
        for m in data["standard_matches"]:
            assert not m["system_id"].startswith("domain_")
            assert m["category"] == "standard"
        for m in data["domain_matches"]:
            assert m["system_id"].startswith("domain_")
            assert m["category"] == "domain"
    _run(_test())
