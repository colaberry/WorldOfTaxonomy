"""Tests for Agricultural Equipment / Machinery domain taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Equipment taxonomy classifies farm machinery and technology -
orthogonal to crop type, livestock category, farming method, and commodity
grade. The same corn crop can be grown with manual tools, a 1970s tractor,
or a GPS-guided autonomous combine with yield monitoring.

Code prefix: dae_
Categories: Tractors and Power Units, Harvesting Equipment, Planting/Seeding,
Irrigation Systems, Livestock Equipment, Precision Ag Technology,
Post-harvest / Storage Equipment.

Stakeholders: equipment dealers, lenders financing ag equipment, insurance
underwriters, USDA NASS equipment surveys, precision ag technology vendors.
Source: USDA NASS Farm Equipment Survey, ASABE standards. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_equipment import (
    AG_EQUIPMENT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_equipment,
)


class TestDetermineLevel:
    def test_tractor_category_is_level_1(self):
        assert _determine_level("dae_tractor") == 1

    def test_row_crop_tractor_is_level_2(self):
        assert _determine_level("dae_tractor_row") == 2

    def test_harvest_category_is_level_1(self):
        assert _determine_level("dae_harvest") == 1

    def test_combine_is_level_2(self):
        assert _determine_level("dae_harvest_combine") == 2

    def test_precision_category_is_level_1(self):
        assert _determine_level("dae_precision") == 1


class TestDetermineParent:
    def test_tractor_category_has_no_parent(self):
        assert _determine_parent("dae_tractor") is None

    def test_row_crop_parent_is_tractor(self):
        assert _determine_parent("dae_tractor_row") == "dae_tractor"

    def test_combine_parent_is_harvest(self):
        assert _determine_parent("dae_harvest_combine") == "dae_harvest"

    def test_precision_gps_parent_is_precision(self):
        assert _determine_parent("dae_precision_gps") == "dae_precision"


class TestAgEquipmentNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_EQUIPMENT_NODES) > 0

    def test_has_tractor_category(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_tractor" in codes

    def test_has_harvesting_category(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_harvest" in codes

    def test_has_planting_category(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_plant" in codes

    def test_has_irrigation_category(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_irrig" in codes

    def test_has_livestock_equipment_category(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_livestock" in codes

    def test_has_precision_ag_category(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_precision" in codes

    def test_has_combine_node(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_harvest_combine" in codes

    def test_has_gps_precision_node(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert "dae_precision_gps" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_EQUIPMENT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_EQUIPMENT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_EQUIPMENT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_EQUIPMENT_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_EQUIPMENT_NODES) >= 25

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_EQUIPMENT_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_equipment_module_importable():
    assert callable(ingest_domain_ag_equipment)
    assert isinstance(AG_EQUIPMENT_NODES, list)


def test_ingest_domain_ag_equipment(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_equipment(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_equipment'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_equipment'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_equipment_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_equipment(conn)
            count2 = await ingest_domain_ag_equipment(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
