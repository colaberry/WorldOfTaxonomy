"""Tests for ICD-10-CM full ingester (97,584 codes from CMS order file)."""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.icd10cm import (
    ingest_icd10cm,
    parse_icd10cm_order_file,
    ICD10CM_CHAPTERS,
)


# ---------------------------------------------------------------------------
# Unit tests for the parser (no DB needed)
# ---------------------------------------------------------------------------

DATA_FILE = "data/icd10cm_order_2025.zip"
HAS_DATA = os.path.exists(DATA_FILE)


class TestIcd10CmChapters:
    """Chapter definitions should be self-consistent."""

    def test_has_22_chapters(self):
        assert len(ICD10CM_CHAPTERS) == 22

    def test_no_duplicate_codes(self):
        codes = [c for c, *_ in ICD10CM_CHAPTERS]
        assert len(codes) == len(set(codes))

    def test_no_em_dashes(self):
        for code, title, _lo, _hi in ICD10CM_CHAPTERS:
            assert "\u2014" not in title


@pytest.mark.skipif(not HAS_DATA, reason="ICD-10-CM data file not found")
class TestIcd10CmParser:
    """Tests against the real CMS order file."""

    def test_parse_returns_nodes(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        assert len(nodes) > 90_000, f"Expected 90K+ nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        codes = [code for code, _title, _level, _parent in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            assert title, f"Empty title for {code}"

    def test_chapters_are_level_1(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        level_1 = [(c, t) for c, t, l, p in nodes if l == 1]
        assert len(level_1) == 22, f"Expected 22 chapters, got {len(level_1)}"
        for code, title in level_1:
            assert code.startswith("CH"), f"Chapter code {code} should start with CH"

    def test_level_1_nodes_have_no_parent(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            if level == 1:
                assert parent is None, f"{code} level-1 has parent {parent}"

    def test_level_2_plus_have_parent(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            if level >= 2:
                assert parent is not None, f"{code} level-{level} missing parent"

    def test_parent_references_valid(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        codes = {c for c, *_ in nodes}
        for code, title, level, parent in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in codes"

    def test_no_em_dashes_in_titles(self):
        nodes = parse_icd10cm_order_file(DATA_FILE)
        for code, title, level, parent in nodes:
            assert "\u2014" not in title, f"Em-dash in {code}: {title}"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------


def test_icd10cm_module_importable():
    assert callable(ingest_icd10cm)


@pytest.mark.skipif(not HAS_DATA, reason="ICD-10-CM data file not found")
def test_ingest_icd10cm(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_icd10cm(conn)
            assert count > 90_000, f"Expected 90K+ nodes, got {count}"
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'icd10cm'"
            )
            assert row is not None
            assert row["node_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(not HAS_DATA, reason="ICD-10-CM data file not found")
def test_ingest_icd10cm_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_icd10cm(conn)
            count2 = await ingest_icd10cm(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
