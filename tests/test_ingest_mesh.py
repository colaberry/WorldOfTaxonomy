"""Tests for MeSH full ingester (31,110 descriptors from NLM XML)."""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.mesh import (
    ingest_mesh,
    parse_mesh_descriptors,
    MESH_CATEGORIES,
)


# ---------------------------------------------------------------------------
# Unit tests (no DB needed)
# ---------------------------------------------------------------------------

DATA_FILE = "data/desc2026.xml"
HAS_DATA = os.path.exists(DATA_FILE)


class TestMeshCategories:
    """Category definitions should be self-consistent."""

    def test_has_16_categories(self):
        assert len(MESH_CATEGORIES) == 16

    def test_no_duplicate_codes(self):
        codes = [c for c, _ in MESH_CATEGORIES]
        assert len(codes) == len(set(codes))

    def test_no_em_dashes(self):
        for code, title in MESH_CATEGORIES:
            assert "\u2014" not in title

    def test_has_diseases_category(self):
        codes = {c for c, _ in MESH_CATEGORIES}
        assert "C" in codes

    def test_has_chemicals_category(self):
        codes = {c for c, _ in MESH_CATEGORIES}
        assert "D" in codes


@pytest.mark.skipif(not HAS_DATA, reason="MeSH data file not found")
class TestMeshParser:
    """Tests against the real NLM descriptor XML."""

    def test_parse_returns_nodes(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        assert len(nodes) > 30_000, f"Expected 30K+ nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        codes = [code for code, _title, _level, _parent in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        for code, title, level, parent in nodes:
            assert title, f"Empty title for {code}"

    def test_categories_are_level_1(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        level_1 = [(c, t) for c, t, l, p in nodes if l == 1]
        assert len(level_1) == 16, f"Expected 16 categories, got {len(level_1)}"

    def test_level_1_nodes_have_no_parent(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        for code, title, level, parent in nodes:
            if level == 1:
                assert parent is None, f"{code} level-1 has parent {parent}"

    def test_level_2_plus_have_parent(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        for code, title, level, parent in nodes:
            if level >= 2:
                assert parent is not None, f"{code} level-{level} missing parent"

    def test_parent_references_valid(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        codes = {c for c, *_ in nodes}
        for code, title, level, parent in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in codes"

    def test_no_em_dashes_in_titles(self):
        nodes = parse_mesh_descriptors(DATA_FILE)
        for code, title, level, parent in nodes:
            assert "\u2014" not in title, f"Em-dash in {code}: {title}"

    def test_descriptor_codes_start_with_d(self):
        """DescriptorUI codes should start with D (not category letters)."""
        nodes = parse_mesh_descriptors(DATA_FILE)
        for code, title, level, parent in nodes:
            if level >= 2:
                assert code.startswith("D"), f"Non-D code at level {level}: {code}"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------


def test_mesh_module_importable():
    assert callable(ingest_mesh)


@pytest.mark.skipif(not HAS_DATA, reason="MeSH data file not found")
def test_ingest_mesh(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_mesh(conn)
            assert count > 30_000, f"Expected 30K+ nodes, got {count}"
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'mesh'"
            )
            assert row is not None
            assert row["node_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(not HAS_DATA, reason="MeSH data file not found")
def test_ingest_mesh_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_mesh(conn)
            count2 = await ingest_mesh(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
