"""Tests for Wholesale Trade Product Category Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_wholesale_product import (
    WHOLESALE_PRODUCT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_wholesale_product,
)


class TestDetermineLevel:
    def test_food_category_is_level_1(self):
        assert _determine_level("dwcprod_food") == 1

    def test_fresh_is_level_2(self):
        assert _determine_level("dwcprod_food_fresh") == 2

    def test_pharma_category_is_level_1(self):
        assert _determine_level("dwcprod_pharma") == 1


class TestDetermineParent:
    def test_food_has_no_parent(self):
        assert _determine_parent("dwcprod_food") is None

    def test_fresh_parent_is_food(self):
        assert _determine_parent("dwcprod_food_fresh") == "dwcprod_food"

    def test_rx_parent_is_pharma(self):
        assert _determine_parent("dwcprod_pharma_rx") == "dwcprod_pharma"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(WHOLESALE_PRODUCT_NODES) > 0

    def test_has_food_category(self):
        codes = [n[0] for n in WHOLESALE_PRODUCT_NODES]
        assert "dwcprod_food" in codes

    def test_has_pharma_category(self):
        codes = [n[0] for n in WHOLESALE_PRODUCT_NODES]
        assert "dwcprod_pharma" in codes

    def test_has_industrial_category(self):
        codes = [n[0] for n in WHOLESALE_PRODUCT_NODES]
        assert "dwcprod_industrial" in codes

    def test_has_fresh_node(self):
        codes = [n[0] for n in WHOLESALE_PRODUCT_NODES]
        assert "dwcprod_food_fresh" in codes

    def test_has_rx_node(self):
        codes = [n[0] for n in WHOLESALE_PRODUCT_NODES]
        assert "dwcprod_pharma_rx" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in WHOLESALE_PRODUCT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in WHOLESALE_PRODUCT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in WHOLESALE_PRODUCT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in WHOLESALE_PRODUCT_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(WHOLESALE_PRODUCT_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in WHOLESALE_PRODUCT_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_wholesale_product)
    assert isinstance(WHOLESALE_PRODUCT_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_wholesale_product(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_wholesale_product'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_wholesale_product(conn)
            count2 = await ingest_domain_wholesale_product(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
