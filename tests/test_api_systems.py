"""Tests for /api/v1/systems endpoints.

TDD RED phase: these tests define the contract for the systems router.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxonomy.api.app import create_app


@pytest.fixture
def app(db_pool):
    """Create a FastAPI app wired to the test database pool."""
    application = create_app()
    application.state.pool = db_pool
    return application


@pytest.fixture
def client(app):
    """Create a test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


def test_list_systems(client):
    async def _test():
        resp = await client.get("/api/v1/systems")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        ids = {s["id"] for s in data}
        assert "naics_2022" in ids
        assert "isic_rev4" in ids
    _run(_test())


def test_system_has_fields(client):
    async def _test():
        resp = await client.get("/api/v1/systems")
        system = resp.json()[0]
        assert "id" in system
        assert "name" in system
        assert "full_name" in system
        assert "node_count" in system
    _run(_test())


def test_get_system_detail(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "naics_2022"
        assert "roots" in data
        assert len(data["roots"]) >= 1
    _run(_test())


def test_get_system_not_found(client):
    async def _test():
        resp = await client.get("/api/v1/systems/nonexistent")
        assert resp.status_code == 404
    _run(_test())


def test_list_systems_query_filter_matches_name(client):
    async def _test():
        resp = await client.get("/api/v1/systems?q=NAICS")
        assert resp.status_code == 200
        data = resp.json()
        ids = {s["id"] for s in data}
        assert "naics_2022" in ids
        for s in data:
            hay = " ".join(
                str(v or "")
                for v in (s.get("id"), s.get("name"), s.get("full_name"),
                          s.get("authority"), s.get("region"))
            ).lower()
            assert "naics" in hay
    _run(_test())


def test_list_systems_query_filter_case_insensitive(client):
    async def _test():
        resp = await client.get("/api/v1/systems?q=naics")
        assert resp.status_code == 200
        ids = {s["id"] for s in resp.json()}
        assert "naics_2022" in ids
    _run(_test())


def test_list_systems_query_no_match(client):
    async def _test():
        resp = await client.get("/api/v1/systems?q=zzzznoneexistingthingzzzz")
        assert resp.status_code == 200
        assert resp.json() == []
    _run(_test())
