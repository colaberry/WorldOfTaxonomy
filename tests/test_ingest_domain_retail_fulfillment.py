"""Tests for Retail Fulfillment and Last-Mile Delivery Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_retail_fulfillment import (
    RETAIL_FULFILLMENT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_retail_fulfillment,
)


class TestDetermineLevel:
    def test_store_category_is_level_1(self):
        assert _determine_level("drcfulfl_store") == 1

    def test_ship_is_level_2(self):
        assert _determine_level("drcfulfl_store_ship") == 2

    def test_direct_category_is_level_1(self):
        assert _determine_level("drcfulfl_direct") == 1


class TestDetermineParent:
    def test_store_has_no_parent(self):
        assert _determine_parent("drcfulfl_store") is None

    def test_ship_parent_is_store(self):
        assert _determine_parent("drcfulfl_store_ship") == "drcfulfl_store"

    def test_3pl_parent_is_direct(self):
        assert _determine_parent("drcfulfl_direct_3pl") == "drcfulfl_direct"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(RETAIL_FULFILLMENT_NODES) > 0

    def test_has_store_category(self):
        codes = [n[0] for n in RETAIL_FULFILLMENT_NODES]
        assert "drcfulfl_store" in codes

    def test_has_direct_category(self):
        codes = [n[0] for n in RETAIL_FULFILLMENT_NODES]
        assert "drcfulfl_direct" in codes

    def test_has_bopis_category(self):
        codes = [n[0] for n in RETAIL_FULFILLMENT_NODES]
        assert "drcfulfl_bopis" in codes

    def test_has_ship_node(self):
        codes = [n[0] for n in RETAIL_FULFILLMENT_NODES]
        assert "drcfulfl_store_ship" in codes

    def test_has_3pl_node(self):
        codes = [n[0] for n in RETAIL_FULFILLMENT_NODES]
        assert "drcfulfl_direct_3pl" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in RETAIL_FULFILLMENT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in RETAIL_FULFILLMENT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in RETAIL_FULFILLMENT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in RETAIL_FULFILLMENT_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(RETAIL_FULFILLMENT_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in RETAIL_FULFILLMENT_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_retail_fulfillment)
    assert isinstance(RETAIL_FULFILLMENT_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_retail_fulfillment(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_retail_fulfillment'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_retail_fulfillment(conn)
            count2 = await ingest_domain_retail_fulfillment(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
