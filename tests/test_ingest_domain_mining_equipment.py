"""Tests for Mining Equipment and Machinery domain taxonomy ingester.

RED tests - written before any implementation exists.

Mining Equipment taxonomy classifies what physical equipment and machinery
is deployed at a mine - orthogonal to mineral type, extraction method, and
reserve classification. The same rope shovel loads copper ore in an open-pit
mine and coal in a surface mine. A rotary drill operates in both gold and
iron ore environments.

Code prefix: dmq_
Categories: Drilling and Blasting Equipment, Loading and Hauling Equipment,
Underground Equipment, Processing and Beneficiation Equipment, Safety and
Support Equipment.

Stakeholders: mining equipment OEMs (Caterpillar, Komatsu, Sandvik, Epiroc),
mine planners doing fleet optimization, equipment finance and insurance,
MSHA equipment inspection, mine safety officers.
Source: SME Mining Engineering Handbook, Caterpillar mining product
classifications, Sandvik product categories. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mining_equipment import (
    MINING_EQUIPMENT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mining_equipment,
)


class TestDetermineLevel:
    def test_drilling_category_is_level_1(self):
        assert _determine_level("dmq_drill") == 1

    def test_rotary_drill_is_level_2(self):
        assert _determine_level("dmq_drill_rotary") == 2

    def test_loading_category_is_level_1(self):
        assert _determine_level("dmq_load") == 1

    def test_haul_truck_is_level_2(self):
        assert _determine_level("dmq_load_haul") == 2

    def test_process_category_is_level_1(self):
        assert _determine_level("dmq_process") == 1


class TestDetermineParent:
    def test_drill_category_has_no_parent(self):
        assert _determine_parent("dmq_drill") is None

    def test_rotary_parent_is_drill(self):
        assert _determine_parent("dmq_drill_rotary") == "dmq_drill"

    def test_haul_parent_is_load(self):
        assert _determine_parent("dmq_load_haul") == "dmq_load"

    def test_crusher_parent_is_process(self):
        assert _determine_parent("dmq_process_crush") == "dmq_process"


class TestMiningEquipmentNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(MINING_EQUIPMENT_NODES) > 0

    def test_has_drilling_category(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert "dmq_drill" in codes

    def test_has_loading_category(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert "dmq_load" in codes

    def test_has_underground_category(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert "dmq_underground" in codes

    def test_has_processing_category(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert "dmq_process" in codes

    def test_has_rotary_drill_node(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert "dmq_drill_rotary" in codes

    def test_has_haul_truck_node(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert "dmq_load_haul" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MINING_EQUIPMENT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MINING_EQUIPMENT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MINING_EQUIPMENT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MINING_EQUIPMENT_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(MINING_EQUIPMENT_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in MINING_EQUIPMENT_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_mining_equipment_module_importable():
    assert callable(ingest_domain_mining_equipment)
    assert isinstance(MINING_EQUIPMENT_NODES, list)


def test_ingest_domain_mining_equipment(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mining_equipment(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mining_equipment'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_mining_equipment'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mining_equipment_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mining_equipment(conn)
            count2 = await ingest_domain_mining_equipment(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
