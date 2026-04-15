"""Tests for NCI Thesaurus full ingester (211K concepts from NCI EVS)."""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.nci_thesaurus import (
    ingest_nci_thesaurus,
    parse_nci_thesaurus,
)


# ---------------------------------------------------------------------------
# Unit tests for the parser (no DB needed)
# ---------------------------------------------------------------------------

DATA_FILE = "data/nci_thesaurus.zip"
HAS_DATA = os.path.exists(DATA_FILE)


@pytest.mark.skipif(not HAS_DATA, reason="NCI Thesaurus data file not found")
class TestNciThesaurusParser:
    """Tests against the real NCI EVS flat file."""

    def test_parse_returns_nodes(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        assert len(nodes) > 200_000, f"Expected 200K+ nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        codes = [code for code, _title, _level, _parent in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        for code, title, level, parent in nodes:
            assert title, f"Empty title for {code}"

    def test_has_root_nodes(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        level_1 = [c for c, t, l, p in nodes if l == 1]
        assert len(level_1) >= 10, f"Expected 10+ roots, got {len(level_1)}"

    def test_level_1_nodes_have_no_parent(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        for code, title, level, parent in nodes:
            if level == 1:
                assert parent is None, f"{code} level-1 has parent {parent}"

    def test_level_2_plus_have_parent(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        for code, title, level, parent in nodes:
            if level >= 2:
                assert parent is not None, f"{code} level-{level} missing parent"

    def test_parent_references_valid(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        codes = {c for c, *_ in nodes}
        for code, title, level, parent in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in codes"

    def test_no_em_dashes_in_titles(self):
        nodes = parse_nci_thesaurus(DATA_FILE)
        for code, title, level, parent in nodes:
            assert "\u2014" not in title, f"Em-dash in {code}: {title}"

    def test_codes_start_with_c(self):
        """NCI Thesaurus concept codes start with C."""
        nodes = parse_nci_thesaurus(DATA_FILE)
        for code, title, level, parent in nodes:
            assert code.startswith("C"), f"Non-C code: {code}"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------


def test_nci_thesaurus_module_importable():
    assert callable(ingest_nci_thesaurus)


@pytest.mark.skipif(not HAS_DATA, reason="NCI Thesaurus data file not found")
def test_ingest_nci_thesaurus(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_nci_thesaurus(conn)
            assert count > 200_000, f"Expected 200K+ nodes, got {count}"
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'nci_thesaurus'"
            )
            assert row is not None
            assert row["node_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(not HAS_DATA, reason="NCI Thesaurus data file not found")
def test_ingest_nci_thesaurus_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_nci_thesaurus(conn)
            count2 = await ingest_nci_thesaurus(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
