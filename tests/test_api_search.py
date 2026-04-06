"""Tests for /api/v1/search endpoint.

TDD RED phase: these tests define the contract for the search router.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxanomy.api.app import create_app


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
