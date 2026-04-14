"""Tests for Food Service and Hospitality Ownership and Franchise Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_food_ownership import (
    FOOD_OWNERSHIP_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_food_ownership,
)


class TestDetermineLevel:
    def test_franchise_category_is_level_1(self):
        assert _determine_level("dfsown_franchise") == 1

    def test_branded_is_level_2(self):
        assert _determine_level("dfsown_franchise_branded") == 2

    def test_managed_category_is_level_1(self):
        assert _determine_level("dfsown_managed") == 1


class TestDetermineParent:
    def test_franchise_has_no_parent(self):
        assert _determine_parent("dfsown_franchise") is None

    def test_branded_parent_is_franchise(self):
        assert _determine_parent("dfsown_franchise_branded") == "dfsown_franchise"

    def test_hotel_parent_is_managed(self):
        assert _determine_parent("dfsown_managed_hotel") == "dfsown_managed"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(FOOD_OWNERSHIP_NODES) > 0

    def test_has_franchise_category(self):
        codes = [n[0] for n in FOOD_OWNERSHIP_NODES]
        assert "dfsown_franchise" in codes

    def test_has_managed_category(self):
        codes = [n[0] for n in FOOD_OWNERSHIP_NODES]
        assert "dfsown_managed" in codes

    def test_has_independent_category(self):
        codes = [n[0] for n in FOOD_OWNERSHIP_NODES]
        assert "dfsown_independent" in codes

    def test_has_branded_node(self):
        codes = [n[0] for n in FOOD_OWNERSHIP_NODES]
        assert "dfsown_franchise_branded" in codes

    def test_has_hotel_node(self):
        codes = [n[0] for n in FOOD_OWNERSHIP_NODES]
        assert "dfsown_managed_hotel" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in FOOD_OWNERSHIP_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in FOOD_OWNERSHIP_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in FOOD_OWNERSHIP_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in FOOD_OWNERSHIP_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(FOOD_OWNERSHIP_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in FOOD_OWNERSHIP_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_food_ownership)
    assert isinstance(FOOD_OWNERSHIP_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_food_ownership(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_food_ownership'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_food_ownership(conn)
            count2 = await ingest_domain_food_ownership(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
