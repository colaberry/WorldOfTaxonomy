"""Tests for /api/v1/systems/{id}/nodes endpoints.

TDD RED phase: these tests define the contract for the nodes router.
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


def test_get_node(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/62")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "62"
        assert data["system_id"] == "naics_2022"
        assert "title" in data
    _run(_test())


def test_get_node_not_found(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/99999")
        assert resp.status_code == 404
    _run(_test())


def test_get_node_children(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/62/children")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for child in data:
            assert "code" in child
            assert "title" in child
    _run(_test())


def test_get_node_ancestors(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/621/ancestors")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        # First should be root (sector 62), last should be 621
        assert data[-1]["code"] == "621"
    _run(_test())


def test_get_node_equivalences(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211/equivalences")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(e["target_system"] == "isic_rev4" for e in data)
    _run(_test())
