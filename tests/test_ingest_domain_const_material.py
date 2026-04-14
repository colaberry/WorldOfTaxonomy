"""Tests for Construction Material Types domain taxonomy ingester.

RED tests - written before any implementation exists.

Construction Material taxonomy classifies the primary structural material
systems used in a building or infrastructure project - orthogonal to trade
type, building type, and delivery method. A high-rise office building, a
hospital, and an industrial warehouse all use structural steel differently;
the same material is designed, fabricated, and erected by the same specialty
trade under any delivery method.

Code prefix: dcmt_
Categories: Structural Wood and Mass Timber, Structural Steel, Concrete and
Masonry, Prefabricated and Modular Systems, Specialty and Advanced Materials.

Stakeholders: structural engineers specifying material systems, material
suppliers and fabricators (AISC, PCI, WoodWorks), building code officials
(IBC fire and structural), sustainable building certification bodies (LEED
material credits), construction cost estimators.
Source: IBC structural material chapters, AISC steel construction classifications,
ACI concrete standards, AWC wood frame construction manual. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_const_material import (
    CONST_MATERIAL_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_const_material,
)


class TestDetermineLevel:
    def test_wood_category_is_level_1(self):
        assert _determine_level("dcmt_wood") == 1

    def test_light_frame_is_level_2(self):
        assert _determine_level("dcmt_wood_lightframe") == 2

    def test_steel_category_is_level_1(self):
        assert _determine_level("dcmt_steel") == 1

    def test_concrete_category_is_level_1(self):
        assert _determine_level("dcmt_concrete") == 1

    def test_cast_in_place_is_level_2(self):
        assert _determine_level("dcmt_concrete_cast") == 2


class TestDetermineParent:
    def test_wood_category_has_no_parent(self):
        assert _determine_parent("dcmt_wood") is None

    def test_light_frame_parent_is_wood(self):
        assert _determine_parent("dcmt_wood_lightframe") == "dcmt_wood"

    def test_cast_parent_is_concrete(self):
        assert _determine_parent("dcmt_concrete_cast") == "dcmt_concrete"

    def test_moment_frame_parent_is_steel(self):
        assert _determine_parent("dcmt_steel_moment") == "dcmt_steel"


class TestConstMaterialNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(CONST_MATERIAL_NODES) > 0

    def test_has_wood_category(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert "dcmt_wood" in codes

    def test_has_steel_category(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert "dcmt_steel" in codes

    def test_has_concrete_category(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert "dcmt_concrete" in codes

    def test_has_prefab_category(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert "dcmt_prefab" in codes

    def test_has_light_frame_node(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert "dcmt_wood_lightframe" in codes

    def test_has_cast_in_place_node(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert "dcmt_concrete_cast" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in CONST_MATERIAL_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in CONST_MATERIAL_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in CONST_MATERIAL_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in CONST_MATERIAL_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(CONST_MATERIAL_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in CONST_MATERIAL_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_const_material_module_importable():
    assert callable(ingest_domain_const_material)
    assert isinstance(CONST_MATERIAL_NODES, list)


def test_ingest_domain_const_material(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_const_material(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_const_material'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_const_material'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_const_material_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_const_material(conn)
            count2 = await ingest_domain_const_material(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
