"""Tests for /api/v1/equivalences endpoints.

TDD RED phase: these tests define the contract for the equivalences router.
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


def test_crosswalk_stats(client):
    async def _test():
        resp = await client.get("/api/v1/equivalences/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        pairs = {(s["source_system"], s["target_system"]) for s in data}
        assert ("naics_2022", "isic_rev4") in pairs
    _run(_test())


def test_crosswalk_stats_fields(client):
    async def _test():
        resp = await client.get("/api/v1/equivalences/stats")
        stat = resp.json()[0]
        assert "source_system" in stat
        assert "target_system" in stat
        assert "edge_count" in stat
        assert "exact_count" in stat
        assert "partial_count" in stat
    _run(_test())
