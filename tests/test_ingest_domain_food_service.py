"""Tests for Food Service and Accommodation domain taxonomy ingester.

RED tests - written before any implementation exists.

Food service and accommodation taxonomy organizes hospitality categories (NAICS 72):
  Lodging Type   (dfs_lodge*)  - full-service hotel, limited-service, extended-stay, motel
  Cuisine Type   (dfs_cuisine*) - American, Italian, Asian, Mexican, Mediterranean
  Service Model  (dfs_svc*)    - fine dining, casual dining, fast casual, QSR, food truck

Source: STR (hospitality benchmarking) + NRA (National Restaurant Association). Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_food_service import (
    FOOD_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_food_service,
)


class TestDetermineLevel:
    def test_lodging_category_is_level_1(self):
        assert _determine_level("dfs_lodge") == 1

    def test_full_service_is_level_2(self):
        assert _determine_level("dfs_lodge_full") == 2

    def test_cuisine_category_is_level_1(self):
        assert _determine_level("dfs_cuisine") == 1

    def test_italian_is_level_2(self):
        assert _determine_level("dfs_cuisine_italian") == 2


class TestDetermineParent:
    def test_lodging_category_has_no_parent(self):
        assert _determine_parent("dfs_lodge") is None

    def test_full_service_parent_is_lodge(self):
        assert _determine_parent("dfs_lodge_full") == "dfs_lodge"

    def test_italian_parent_is_cuisine(self):
        assert _determine_parent("dfs_cuisine_italian") == "dfs_cuisine"


class TestFoodNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(FOOD_NODES) > 0

    def test_has_lodging_category(self):
        codes = [n[0] for n in FOOD_NODES]
        assert "dfs_lodge" in codes

    def test_has_cuisine_category(self):
        codes = [n[0] for n in FOOD_NODES]
        assert "dfs_cuisine" in codes

    def test_has_service_model_category(self):
        codes = [n[0] for n in FOOD_NODES]
        assert "dfs_svc" in codes

    def test_has_full_service_hotel(self):
        codes = [n[0] for n in FOOD_NODES]
        assert "dfs_lodge_full" in codes

    def test_has_qsr(self):
        codes = [n[0] for n in FOOD_NODES]
        assert "dfs_svc_qsr" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in FOOD_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in FOOD_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in FOOD_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in FOOD_NODES:
            if level == 2:
                assert parent is not None


def test_domain_food_service_module_importable():
    assert callable(ingest_domain_food_service)
    assert isinstance(FOOD_NODES, list)


def test_ingest_domain_food_service(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_food_service(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_food_service'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_food_service_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_food_service(conn)
            count2 = await ingest_domain_food_service(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
