"""Tests for Manufacturing Industry Vertical domain taxonomy ingester.

RED tests - written before any implementation exists.

Manufacturing Industry Vertical classifies WHAT is being made - orthogonal
to HOW it's made (process types already in domain_mfg_process). The same
CNC machining process produces aerospace fasteners, medical implants, and
auto brake calipers - different regulatory environments, buyer requirements,
and supply chain structures for each end-market.

Code prefix: dfpi_
Categories: Automotive and Transportation Equipment, Aerospace and Defense,
Electronics and Semiconductors, Life Sciences and Medical Devices,
Food and Beverage, Chemical and Materials, Industrial Equipment.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mfg_industry import (
    MFG_INDUSTRY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mfg_industry,
)


class TestDetermineLevel:
    def test_auto_category_is_level_1(self):
        assert _determine_level("dfpi_auto") == 1

    def test_oem_is_level_2(self):
        assert _determine_level("dfpi_auto_oem") == 2

    def test_aero_category_is_level_1(self):
        assert _determine_level("dfpi_aero") == 1

    def test_life_category_is_level_1(self):
        assert _determine_level("dfpi_life") == 1


class TestDetermineParent:
    def test_auto_has_no_parent(self):
        assert _determine_parent("dfpi_auto") is None

    def test_oem_parent_is_auto(self):
        assert _determine_parent("dfpi_auto_oem") == "dfpi_auto"

    def test_implant_parent_is_life(self):
        assert _determine_parent("dfpi_life_implant") == "dfpi_life"


class TestMfgIndustryNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(MFG_INDUSTRY_NODES) > 0

    def test_has_auto_category(self):
        codes = [n[0] for n in MFG_INDUSTRY_NODES]
        assert "dfpi_auto" in codes

    def test_has_aero_category(self):
        codes = [n[0] for n in MFG_INDUSTRY_NODES]
        assert "dfpi_aero" in codes

    def test_has_electronics_category(self):
        codes = [n[0] for n in MFG_INDUSTRY_NODES]
        assert "dfpi_elec" in codes

    def test_has_life_sciences_category(self):
        codes = [n[0] for n in MFG_INDUSTRY_NODES]
        assert "dfpi_life" in codes

    def test_has_food_category(self):
        codes = [n[0] for n in MFG_INDUSTRY_NODES]
        assert "dfpi_food" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MFG_INDUSTRY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MFG_INDUSTRY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MFG_INDUSTRY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MFG_INDUSTRY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(MFG_INDUSTRY_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in MFG_INDUSTRY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_mfg_industry_module_importable():
    assert callable(ingest_domain_mfg_industry)
    assert isinstance(MFG_INDUSTRY_NODES, list)


def test_ingest_domain_mfg_industry(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mfg_industry(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mfg_industry'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mfg_industry_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mfg_industry(conn)
            count2 = await ingest_domain_mfg_industry(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
