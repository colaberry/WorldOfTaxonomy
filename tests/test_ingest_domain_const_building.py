"""Tests for Construction Building Type domain taxonomy ingester.

RED tests - written before any implementation exists.

Building type taxonomy uses IBC (International Building Code) occupancy:
  Residential  (dcb_resid*)  - single-family, multi-family, mixed-use
  Commercial   (dcb_comm*)   - office, retail, hotel, restaurant
  Industrial   (dcb_indust*) - manufacturing, warehouse, utility
  Institutional (dcb_inst*)  - healthcare, education, government, recreation

Source: International Building Code (IBC) occupancy classifications. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_const_building import (
    BUILDING_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_const_building,
)


class TestDetermineLevel:
    def test_residential_category_is_level_1(self):
        assert _determine_level("dcb_resid") == 1

    def test_single_family_is_level_2(self):
        assert _determine_level("dcb_resid_single") == 2

    def test_commercial_category_is_level_1(self):
        assert _determine_level("dcb_comm") == 1

    def test_office_is_level_2(self):
        assert _determine_level("dcb_comm_office") == 2


class TestDetermineParent:
    def test_residential_category_has_no_parent(self):
        assert _determine_parent("dcb_resid") is None

    def test_single_family_parent_is_resid(self):
        assert _determine_parent("dcb_resid_single") == "dcb_resid"

    def test_office_parent_is_comm(self):
        assert _determine_parent("dcb_comm_office") == "dcb_comm"


class TestBuildingNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(BUILDING_NODES) > 0

    def test_has_residential_category(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert "dcb_resid" in codes

    def test_has_commercial_category(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert "dcb_comm" in codes

    def test_has_industrial_category(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert "dcb_indust" in codes

    def test_has_institutional_category(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert "dcb_inst" in codes

    def test_has_office(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert "dcb_comm_office" in codes

    def test_has_single_family(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert "dcb_resid_single" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in BUILDING_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in BUILDING_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in BUILDING_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in BUILDING_NODES:
            if level == 2:
                assert parent is not None


def test_domain_const_building_module_importable():
    assert callable(ingest_domain_const_building)
    assert isinstance(BUILDING_NODES, list)


def test_ingest_domain_const_building(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_const_building(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_const_building'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_const_building_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_const_building(conn)
            count2 = await ingest_domain_const_building(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
