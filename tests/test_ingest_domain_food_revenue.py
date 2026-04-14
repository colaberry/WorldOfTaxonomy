"""Tests for Food Service and Hospitality Revenue Management Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_food_revenue import (
    FOOD_REVENUE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_food_revenue,
)


class TestDetermineLevel:
    def test_room_category_is_level_1(self):
        assert _determine_level("dfsrev_room") == 1

    def test_revpar_is_level_2(self):
        assert _determine_level("dfsrev_room_revpar") == 2

    def test_fb_category_is_level_1(self):
        assert _determine_level("dfsrev_fb") == 1


class TestDetermineParent:
    def test_room_has_no_parent(self):
        assert _determine_parent("dfsrev_room") is None

    def test_revpar_parent_is_room(self):
        assert _determine_parent("dfsrev_room_revpar") == "dfsrev_room"

    def test_covers_parent_is_fb(self):
        assert _determine_parent("dfsrev_fb_covers") == "dfsrev_fb"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(FOOD_REVENUE_NODES) > 0

    def test_has_room_category(self):
        codes = [n[0] for n in FOOD_REVENUE_NODES]
        assert "dfsrev_room" in codes

    def test_has_fb_category(self):
        codes = [n[0] for n in FOOD_REVENUE_NODES]
        assert "dfsrev_fb" in codes

    def test_has_event_category(self):
        codes = [n[0] for n in FOOD_REVENUE_NODES]
        assert "dfsrev_event" in codes

    def test_has_revpar_node(self):
        codes = [n[0] for n in FOOD_REVENUE_NODES]
        assert "dfsrev_room_revpar" in codes

    def test_has_covers_node(self):
        codes = [n[0] for n in FOOD_REVENUE_NODES]
        assert "dfsrev_fb_covers" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in FOOD_REVENUE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in FOOD_REVENUE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in FOOD_REVENUE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in FOOD_REVENUE_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(FOOD_REVENUE_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in FOOD_REVENUE_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_food_revenue)
    assert isinstance(FOOD_REVENUE_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_food_revenue(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_food_revenue'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_food_revenue(conn)
            count2 = await ingest_domain_food_revenue(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
