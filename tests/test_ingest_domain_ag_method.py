"""Tests for Agriculture Farming Method domain taxonomy ingester.

RED tests - written before any implementation exists.

Farming method taxonomy organizes production practices into categories:
  Production System (dam_sys*)   - conventional, organic, biodynamic, hydroponic
  Scale             (dam_scale*)  - smallholder, family farm, commercial, corporate
  Irrigation        (dam_irr*)   - dryland, irrigated, drip, flood, sprinkler
  Tillage           (dam_till*)  - conventional till, no-till, strip-till, reduced
  Certification     (dam_cert*)  - USDA organic, GAP, fair trade, non-GMO

Source: USDA NASS + NOP (National Organic Program). Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_method import (
    METHOD_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_method,
)


class TestDetermineLevel:
    def test_system_category_is_level_1(self):
        assert _determine_level("dam_sys") == 1

    def test_system_type_is_level_2(self):
        assert _determine_level("dam_sys_organic") == 2

    def test_scale_category_is_level_1(self):
        assert _determine_level("dam_scale") == 1

    def test_scale_type_is_level_2(self):
        assert _determine_level("dam_scale_family") == 2


class TestDetermineParent:
    def test_system_category_has_no_parent(self):
        assert _determine_parent("dam_sys") is None

    def test_organic_parent_is_system(self):
        assert _determine_parent("dam_sys_organic") == "dam_sys"

    def test_scale_type_parent_is_scale(self):
        assert _determine_parent("dam_scale_family") == "dam_scale"


class TestMethodNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(METHOD_NODES) > 0

    def test_has_system_category(self):
        codes = [n[0] for n in METHOD_NODES]
        assert "dam_sys" in codes

    def test_has_scale_category(self):
        codes = [n[0] for n in METHOD_NODES]
        assert "dam_scale" in codes

    def test_has_organic(self):
        codes = [n[0] for n in METHOD_NODES]
        assert "dam_sys_organic" in codes

    def test_has_conventional(self):
        codes = [n[0] for n in METHOD_NODES]
        assert "dam_sys_conventional" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in METHOD_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in METHOD_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in METHOD_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in METHOD_NODES:
            if level == 2:
                assert parent is not None


def test_domain_ag_method_module_importable():
    assert callable(ingest_domain_ag_method)
    assert isinstance(METHOD_NODES, list)


def test_ingest_domain_ag_method(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_method(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_method'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_method_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_method(conn)
            count2 = await ingest_domain_ag_method(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
