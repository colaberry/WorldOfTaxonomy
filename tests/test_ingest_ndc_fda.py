"""Tests for NDC full ingester (112K products from FDA directory)."""
import asyncio
import os

import pytest

from world_of_taxonomy.ingest.ndc_fda import (
    ingest_ndc_fda,
    parse_ndc_products,
    NDC_PRODUCT_TYPES,
)


# ---------------------------------------------------------------------------
# Unit tests for the parser (no DB needed)
# ---------------------------------------------------------------------------

DATA_FILE = "data/ndc_product.zip"
HAS_DATA = os.path.exists(DATA_FILE)


class TestNdcProductTypes:
    """Product type definitions should be self-consistent."""

    def test_has_product_types(self):
        assert len(NDC_PRODUCT_TYPES) >= 5

    def test_no_duplicate_codes(self):
        codes = [c for c, _ in NDC_PRODUCT_TYPES]
        assert len(codes) == len(set(codes))

    def test_no_em_dashes(self):
        for code, title in NDC_PRODUCT_TYPES:
            assert "\u2014" not in title


@pytest.mark.skipif(not HAS_DATA, reason="NDC data file not found")
class TestNdcParser:
    """Tests against the real FDA NDC directory."""

    def test_parse_returns_nodes(self):
        nodes = parse_ndc_products(DATA_FILE)
        assert len(nodes) > 100_000, f"Expected 100K+ nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_ndc_products(DATA_FILE)
        codes = [code for code, _title, _level, _parent in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_ndc_products(DATA_FILE)
        for code, title, level, parent in nodes:
            assert title, f"Empty title for {code}"

    def test_level_1_are_product_types(self):
        nodes = parse_ndc_products(DATA_FILE)
        level_1 = [(c, t) for c, t, l, p in nodes if l == 1]
        assert len(level_1) >= 5, f"Expected 5+ product types, got {len(level_1)}"

    def test_level_1_nodes_have_no_parent(self):
        nodes = parse_ndc_products(DATA_FILE)
        for code, title, level, parent in nodes:
            if level == 1:
                assert parent is None, f"{code} level-1 has parent {parent}"

    def test_level_2_plus_have_parent(self):
        nodes = parse_ndc_products(DATA_FILE)
        for code, title, level, parent in nodes:
            if level >= 2:
                assert parent is not None, f"{code} level-{level} missing parent"

    def test_parent_references_valid(self):
        nodes = parse_ndc_products(DATA_FILE)
        codes = {c for c, *_ in nodes}
        for code, title, level, parent in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in codes"

    def test_no_em_dashes_in_titles(self):
        nodes = parse_ndc_products(DATA_FILE)
        for code, title, level, parent in nodes:
            assert "\u2014" not in title, f"Em-dash in {code}: {title}"


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------


def test_ndc_fda_module_importable():
    assert callable(ingest_ndc_fda)


@pytest.mark.skipif(not HAS_DATA, reason="NDC data file not found")
def test_ingest_ndc_fda(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_ndc_fda(conn)
            assert count > 100_000, f"Expected 100K+ nodes, got {count}"
            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'ndc_fda'"
            )
            assert row is not None
            assert row["node_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(not HAS_DATA, reason="NDC data file not found")
def test_ingest_ndc_fda_idempotent(db_pool):
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_ndc_fda(conn)
            count2 = await ingest_ndc_fda(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
