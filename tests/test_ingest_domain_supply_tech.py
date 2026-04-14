"""Tests for Supply Chain Technology Platform Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_supply_tech import (
    SUPPLY_TECH_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_supply_tech,
)


class TestDetermineLevel:
    def test_tms_category_is_level_1(self):
        assert _determine_level("dsctech_tms") == 1

    def test_cloud_is_level_2(self):
        assert _determine_level("dsctech_tms_cloud") == 2

    def test_wms_category_is_level_1(self):
        assert _determine_level("dsctech_wms") == 1


class TestDetermineParent:
    def test_tms_has_no_parent(self):
        assert _determine_parent("dsctech_tms") is None

    def test_cloud_parent_is_tms(self):
        assert _determine_parent("dsctech_tms_cloud") == "dsctech_tms"

    def test_realtime_parent_is_wms(self):
        assert _determine_parent("dsctech_visibility_realtime") == "dsctech_visibility"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(SUPPLY_TECH_NODES) > 0

    def test_has_tms_category(self):
        codes = [n[0] for n in SUPPLY_TECH_NODES]
        assert "dsctech_tms" in codes

    def test_has_wms_category(self):
        codes = [n[0] for n in SUPPLY_TECH_NODES]
        assert "dsctech_wms" in codes

    def test_has_oms_category(self):
        codes = [n[0] for n in SUPPLY_TECH_NODES]
        assert "dsctech_oms" in codes

    def test_has_cloud_node(self):
        codes = [n[0] for n in SUPPLY_TECH_NODES]
        assert "dsctech_tms_cloud" in codes

    def test_has_realtime_node(self):
        codes = [n[0] for n in SUPPLY_TECH_NODES]
        assert "dsctech_visibility_realtime" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in SUPPLY_TECH_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in SUPPLY_TECH_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in SUPPLY_TECH_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in SUPPLY_TECH_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(SUPPLY_TECH_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in SUPPLY_TECH_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_supply_tech)
    assert isinstance(SUPPLY_TECH_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_supply_tech(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_supply_tech'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_supply_tech(conn)
            count2 = await ingest_domain_supply_tech(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
