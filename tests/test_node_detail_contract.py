"""Node detail page - API contract tests.

RED phase: pin the exact contract consumed by /system/[id]/node/[code].
These tests must be GREEN before the frontend page is built.

Covers:
  - Full ancestor chain ordering
  - Leaf vs non-leaf consistency
  - Description field presence
  - Equivalences with titles
  - Hyphenated codes (NAICS 31-33) work in URL paths
  - Root node has no parent in ancestor chain
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


# ── Ancestor chain ────────────────────────────────────────────


def test_deep_node_full_ancestor_chain(client):
    """5-level deep node returns all 5 ancestors, root-first."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/111110/ancestors")
        assert resp.status_code == 200
        codes = [n["code"] for n in resp.json()]
        assert codes == ["11", "111", "1111", "11111", "111110"]
    _run(_test())


def test_ancestors_ordered_root_first(client):
    """Ancestors list starts at root (level 1) and ends at the queried node."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211/ancestors")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["code"] == "62"      # root
        assert data[-1]["code"] == "6211"   # self
        levels = [n["level"] for n in data]
        assert levels == sorted(levels)     # strictly ascending
    _run(_test())


def test_root_node_ancestor_chain_is_just_self(client):
    """A root node returns only itself in ancestors."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/11/ancestors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["code"] == "11"
        assert data[0]["parent_code"] is None
    _run(_test())


# ── Leaf / non-leaf consistency ───────────────────────────────


def test_leaf_flag_true_and_children_empty(client):
    """is_leaf=True node must return empty children list."""
    async def _test():
        node_resp = await client.get("/api/v1/systems/naics_2022/nodes/111110")
        assert node_resp.json()["is_leaf"] is True

        children_resp = await client.get("/api/v1/systems/naics_2022/nodes/111110/children")
        assert children_resp.status_code == 200
        assert children_resp.json() == []
    _run(_test())


def test_nonleaf_flag_false_and_children_present(client):
    """is_leaf=False node must return non-empty children list."""
    async def _test():
        node_resp = await client.get("/api/v1/systems/naics_2022/nodes/62")
        assert node_resp.json()["is_leaf"] is False

        children_resp = await client.get("/api/v1/systems/naics_2022/nodes/62/children")
        assert children_resp.status_code == 200
        assert len(children_resp.json()) >= 1
    _run(_test())


# ── Description ───────────────────────────────────────────────


def test_node_description_returned_when_present(client):
    """Nodes with descriptions return them; nodes without return null."""
    async def _test():
        # 6211 has description in seed data
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211")
        data = resp.json()
        assert "description" in data
        assert data["description"] == "Establishments with M.D. or D.O. degrees"

        # 621 has no description
        resp2 = await client.get("/api/v1/systems/naics_2022/nodes/621")
        assert resp2.json()["description"] is None
    _run(_test())


# ── Equivalences ──────────────────────────────────────────────


def test_equivalences_include_source_and_target_titles(client):
    """Equivalence edges must include source_title and target_title for UI display."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211/equivalences")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        for edge in data:
            assert "source_title" in edge
            assert "target_title" in edge
            assert edge["source_title"] is not None
            assert edge["target_title"] is not None
    _run(_test())


def test_equivalences_include_match_type(client):
    """match_type field must be present - UI uses it to show exact vs partial badges."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211/equivalences")
        data = resp.json()
        assert all("match_type" in e for e in data)
        assert all(e["match_type"] in ("exact", "partial", "broad", "narrow") for e in data)
    _run(_test())


# ── Hyphenated codes ──────────────────────────────────────────


def test_hyphenated_code_accessible(client):
    """NAICS '31-33' contains a hyphen - must be reachable via URL path."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/31-33")
        assert resp.status_code == 200
        assert resp.json()["code"] == "31-33"
    _run(_test())


def test_hyphenated_code_children_accessible(client):
    """Children of a hyphenated-code node must be reachable."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/31-33/children")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    _run(_test())


def test_hyphenated_code_ancestors_accessible(client):
    """Ancestors of a hyphenated-code node must be reachable."""
    async def _test():
        resp = await client.get("/api/v1/systems/naics_2022/nodes/31-33/ancestors")
        assert resp.status_code == 200
        data = resp.json()
        assert data[-1]["code"] == "31-33"
    _run(_test())
