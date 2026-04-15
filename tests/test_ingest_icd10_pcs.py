"""Tests for ICD-10-PCS full ingester (79,856 codes from CMS order file)."""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.icd10_pcs import (
    ingest_icd10_pcs,
    parse_icd10pcs_order_file,
    ICD10PCS_SECTIONS,
)


# ---------------------------------------------------------------------------
# Unit tests for the parser (no DB needed)
# ---------------------------------------------------------------------------

DATA_FILE = "data/icd10pcs_order_2025.zip"
HAS_DATA = os.path.exists(DATA_FILE)


class TestIcd10PcsSections:
    """Section definitions should be self-consistent."""

    def test_has_17_sections(self):
        assert len(ICD10PCS_SECTIONS) == 17

    def test_no_duplicate_codes(self):
        codes = [c for c, _ in ICD10PCS_SECTIONS]
        assert len(codes) == len(set(codes))

    def test_no_em_dashes(self):
        for code, title in ICD10PCS_SECTIONS:
            assert "\u2014" not in title


@pytest.mark.skipif(not HAS_DATA, reason="ICD-10-PCS data file not found")
class TestIcd10PcsParser:
    """Tests against the real CMS order file."""

    def test_parse_returns_nodes(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        assert len(nodes) > 75_000, f"Expected 75K+ nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        codes = [code for code, _title, _level, _parent in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            assert title, f"Empty title for {code}"

    def test_sections_are_level_1(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        level_1 = [(c, t) for c, t, l, p in nodes if l == 1]
        assert len(level_1) == 17, f"Expected 17 sections, got {len(level_1)}"

    def test_level_1_nodes_have_no_parent(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            if level == 1:
                assert parent is None, f"{code} level-1 has parent {parent}"

    def test_level_2_plus_have_parent(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            if level >= 2:
                assert parent is not None, f"{code} level-{level} missing parent"

    def test_parent_references_valid(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        codes = {c for c, *_ in nodes}
        for code, title, level, parent in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in codes"

    def test_no_em_dashes_in_titles(self):
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            assert "\u2014" not in title, f"Em-dash in {code}: {title}"

    def test_hierarchy_levels(self):
        """Verify expected level distribution."""
        nodes = parse_icd10pcs_order_file(DATA_FILE)
        from collections import Counter
        levels = Counter(l for _, _, l, _ in nodes)
        assert levels[1] == 17, "17 sections at level 1"
        assert levels[2] > 50, "Body systems at level 2"
        assert levels[3] == 908, "908 root-operation tables at level 3"
        assert levels[4] > 70_000, "Full codes at level 4"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------


def test_icd10_pcs_module_importable():
    assert callable(ingest_icd10_pcs)


@pytest.mark.skipif(not HAS_DATA, reason="ICD-10-PCS data file not found")
def test_ingest_icd10_pcs(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_icd10_pcs(conn)
            assert count > 75_000, f"Expected 75K+ nodes, got {count}"
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'icd10_pcs'"
            )
            assert row is not None
            assert row["node_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(not HAS_DATA, reason="ICD-10-PCS data file not found")
def test_ingest_icd10_pcs_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_icd10_pcs(conn)
            count2 = await ingest_icd10_pcs(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
