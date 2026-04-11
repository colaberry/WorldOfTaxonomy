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


def test_stats_returns_both_directions(client):
    """Stats returns both A→B and B→A - deduplication is a frontend concern."""
    async def _test():
        resp = await client.get("/api/v1/equivalences/stats")
        pairs = {(s["source_system"], s["target_system"]) for s in resp.json()}
        assert ("naics_2022", "isic_rev4") in pairs
        assert ("isic_rev4", "naics_2022") in pairs
    _run(_test())


def test_stats_symmetric_edge_counts(client):
    """Both directions of a pair have identical counts - safe to deduplicate."""
    async def _test():
        resp = await client.get("/api/v1/equivalences/stats")
        by_pair = {(s["source_system"], s["target_system"]): s for s in resp.json()}
        fwd = by_pair.get(("naics_2022", "isic_rev4"))
        rev = by_pair.get(("isic_rev4", "naics_2022"))
        assert fwd is not None and rev is not None
        assert fwd["edge_count"] == rev["edge_count"]
        assert fwd["exact_count"] == rev["exact_count"]
        assert fwd["partial_count"] == rev["partial_count"]
    _run(_test())


def test_stats_no_self_loops(client):
    """No system should have a crosswalk edge to itself."""
    async def _test():
        resp = await client.get("/api/v1/equivalences/stats")
        for s in resp.json():
            assert s["source_system"] != s["target_system"]
    _run(_test())
