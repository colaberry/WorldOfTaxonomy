"""Tests for new explore/cross-system API endpoints - RED phase.

Endpoints:
  GET /api/v1/systems/{id}/nodes/{code}/translations
  GET /api/v1/systems/{id}/nodes/{code}/siblings
  GET /api/v1/systems/{id}/nodes/{code}/subtree
  GET /api/v1/compare?a={sys}&b={sys}
  GET /api/v1/search?q=&grouped=true
  GET /api/v1/equivalences/stats?system_id={id}
  GET /api/v1/diff?a={sys}&b={sys}
  GET /api/v1/nodes/{code}
  GET /api/v1/systems/stats
  GET /api/v1/systems?group_by=region
  GET /api/v1/search?q=&context=true
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


# ── GET /api/v1/systems/{id}/nodes/{code}/translations ────────


def test_translations_returns_all_equivalences(client):
    """All cross-system mappings for a code in one call."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211/translations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for item in data:
            assert "target_system" in item
            assert "target_code" in item
            assert "match_type" in item
            assert "target_title" in item
    _run(_test())


def test_translations_empty_for_unmapped_code(client):
    """Code with no crosswalk edges returns empty list."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/62/translations")
        assert resp.status_code == 200
        assert resp.json() == []
    _run(_test())


def test_translations_404_for_unknown_node(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/99999/translations")
        assert resp.status_code == 404
    _run(_test())


# ── GET /api/v1/systems/{id}/nodes/{code}/siblings ────────────


def test_siblings_returns_list(client):
    """Siblings share the same parent."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/621/siblings")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # node itself should NOT appear
        codes = [n["code"] for n in data]
        assert "621" not in codes
    _run(_test())


def test_siblings_404_for_unknown_node(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/99999/siblings")
        assert resp.status_code == 404
    _run(_test())


# ── GET /api/v1/systems/{id}/nodes/{code}/subtree ─────────────


def test_subtree_returns_summary(client):
    """Subtree summary: total, leaf count, max depth."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/62/subtree")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "62"
        assert data["total_nodes"] >= 1
        assert data["leaf_count"] >= 1
        assert "max_depth" in data
    _run(_test())


def test_subtree_404_for_unknown_node(client):
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/99999/subtree")
        assert resp.status_code == 404
    _run(_test())


# ── GET /api/v1/compare?a={sys}&b={sys} ───────────────────────


def test_compare_systems(client):
    """Side-by-side top-level sectors."""
    async def _test():
        resp = await client.get("/api/v1/compare?a=naics_2022&b=isic_rev4")
        assert resp.status_code == 200
        data = resp.json()
        assert "system_a" in data
        assert "system_b" in data
        assert isinstance(data["system_a"], list)
        assert isinstance(data["system_b"], list)
        assert len(data["system_a"]) >= 1
        assert len(data["system_b"]) >= 1
    _run(_test())


def test_compare_missing_param(client):
    async def _test():
        resp = await client.get("/api/v1/compare?a=naics_2022")
        assert resp.status_code == 422
    _run(_test())


def test_compare_unknown_system(client):
    async def _test():
        resp = await client.get("/api/v1/compare?a=naics_2022&b=nonexistent")
        assert resp.status_code == 404
    _run(_test())


# ── GET /api/v1/search?q=&grouped=true ───────────────────────


def test_search_grouped(client):
    """Grouped search returns dict keyed by system_id."""
    async def _test():
        resp = await client.get("/api/v1/search?q=agriculture&grouped=true")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        for system_id, matches in data.items():
            assert isinstance(matches, list)
            for m in matches:
                assert m["system_id"] == system_id
        assert "naics_2022" in data
    _run(_test())


def test_search_grouped_false_returns_list(client):
    """Default (grouped=false) still returns flat list."""
    async def _test():
        resp = await client.get("/api/v1/search?q=agriculture")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    _run(_test())


# ── GET /api/v1/equivalences/stats?system_id= ────────────────


def test_equivalences_stats_filtered(client):
    """Filter stats to a specific system."""
    async def _test():
        resp = await client.get("/api/v1/equivalences/stats?system_id=naics_2022")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for entry in data:
            assert (entry["source_system"] == "naics_2022" or
                    entry["target_system"] == "naics_2022")
    _run(_test())


# ── GET /api/v1/diff?a={sys}&b={sys} ─────────────────────────


def test_diff_returns_unmapped_nodes(client):
    """Nodes in A with no equivalence to B."""
    async def _test():
        resp = await client.get("/api/v1/diff?a=naics_2022&b=isic_rev4")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for node in data:
            assert node["system_id"] == "naics_2022"
            assert "code" in node
            assert "title" in node
    _run(_test())


def test_diff_missing_param(client):
    async def _test():
        resp = await client.get("/api/v1/diff?a=naics_2022")
        assert resp.status_code == 422
    _run(_test())


# ── GET /api/v1/nodes/{code} ──────────────────────────────────


def test_cross_system_lookup(client):
    """Find all systems containing a given code."""
    async def _test():
        resp = await client.get("/api/v1/nodes/0111")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        system_ids = {n["system_id"] for n in data}
        assert "isic_rev4" in system_ids
        assert "sic_1987" in system_ids
    _run(_test())


def test_cross_system_lookup_unique(client):
    """Code in only one system returns single-item list."""
    async def _test():
        resp = await client.get("/api/v1/nodes/6211")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["system_id"] == "naics_2022"
    _run(_test())


def test_cross_system_lookup_not_found(client):
    async def _test():
        resp = await client.get("/api/v1/nodes/ZZZZ99")
        assert resp.status_code == 404
    _run(_test())


# ── GET /api/v1/systems/stats ─────────────────────────────────


def test_systems_stats(client):
    """Per-system leaf/total counts."""
    async def _test():
        resp = await client.get("/api/v1/systems/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        for entry in data:
            assert "system_id" in entry
            assert "total_nodes" in entry
            assert "leaf_nodes" in entry
            assert entry["leaf_nodes"] <= entry["total_nodes"]
    _run(_test())


# ── GET /api/v1/systems?group_by=region ──────────────────────


def test_systems_grouped_by_region(client):
    """Systems grouped by region."""
    async def _test():
        resp = await client.get("/api/v1/systems?group_by=region")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        for region, systems in data.items():
            assert isinstance(systems, list)
            for s in systems:
                assert "id" in s
                assert "name" in s
        all_ids = [s["id"] for systems in data.values() for s in systems]
        assert "naics_2022" in all_ids
    _run(_test())


def test_systems_no_group_by_returns_list(client):
    """Without group_by, returns flat list as before."""
    async def _test():
        resp = await client.get("/api/v1/systems")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    _run(_test())


# ── GET /api/v1/search?q=&context=true ───────────────────────


def test_search_with_context(client):
    """Each match includes ancestors and children."""
    async def _test():
        resp = await client.get("/api/v1/search?q=physician&context=true")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for item in data:
            assert "ancestors" in item
            assert "children" in item
            assert isinstance(item["ancestors"], list)
            assert isinstance(item["children"], list)
    _run(_test())


def test_search_context_ancestors_root_first(client):
    """Ancestors ordered root → parent."""
    async def _test():
        resp = await client.get(
            "/api/v1/search?q=soybean&context=true&system_id=naics_2022"
        )
        assert resp.status_code == 200
        data = resp.json()
        entry = next((e for e in data if e["code"] == "111110"), None)
        if entry:
            ancestors = entry["ancestors"]
            assert len(ancestors) >= 2
            assert ancestors[0]["level"] <= ancestors[-1]["level"]
    _run(_test())
