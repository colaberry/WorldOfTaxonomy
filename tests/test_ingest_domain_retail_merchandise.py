"""Tests for Retail Merchandise and Product Category Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_retail_merchandise import (
    RETAIL_MERCH_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_retail_merchandise,
)


class TestDetermineLevel:
    def test_grocery_category_is_level_1(self):
        assert _determine_level("drcmerch_grocery") == 1

    def test_fresh_is_level_2(self):
        assert _determine_level("drcmerch_grocery_fresh") == 2

    def test_apparel_category_is_level_1(self):
        assert _determine_level("drcmerch_apparel") == 1


class TestDetermineParent:
    def test_grocery_has_no_parent(self):
        assert _determine_parent("drcmerch_grocery") is None

    def test_fresh_parent_is_grocery(self):
        assert _determine_parent("drcmerch_grocery_fresh") == "drcmerch_grocery"

    def test_fast_parent_is_apparel(self):
        assert _determine_parent("drcmerch_apparel_fast") == "drcmerch_apparel"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(RETAIL_MERCH_NODES) > 0

    def test_has_grocery_category(self):
        codes = [n[0] for n in RETAIL_MERCH_NODES]
        assert "drcmerch_grocery" in codes

    def test_has_apparel_category(self):
        codes = [n[0] for n in RETAIL_MERCH_NODES]
        assert "drcmerch_apparel" in codes

    def test_has_electronics_category(self):
        codes = [n[0] for n in RETAIL_MERCH_NODES]
        assert "drcmerch_electronics" in codes

    def test_has_fresh_node(self):
        codes = [n[0] for n in RETAIL_MERCH_NODES]
        assert "drcmerch_grocery_fresh" in codes

    def test_has_fast_node(self):
        codes = [n[0] for n in RETAIL_MERCH_NODES]
        assert "drcmerch_apparel_fast" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in RETAIL_MERCH_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in RETAIL_MERCH_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in RETAIL_MERCH_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in RETAIL_MERCH_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(RETAIL_MERCH_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in RETAIL_MERCH_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_retail_merchandise)
    assert isinstance(RETAIL_MERCH_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_retail_merchandise(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_retail_merchandise'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_retail_merchandise(conn)
            count2 = await ingest_domain_retail_merchandise(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
