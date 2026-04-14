"""Tests for Agricultural Land / Soil / Climate Classification taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Land taxonomy classifies the physical environment where farming
occurs - orthogonal to what's grown, how it's grown, what equipment is used,
and what inputs are applied. The same farming method applied to Class I
irrigated bottomland in the Central Valley produces very differently than
on Class VI dryland in the Great Plains.

Code prefix: dal_ (ag land - note: same prefix as domain_ag_livestock's dal_)

To avoid collision with domain_ag_livestock (dal_*), use prefix: daln_

Code prefix: daln_
Categories: USDA Land Capability Class, Major Agricultural Region / Growing Zone,
Soil Type, Water Availability / Hydrology, Climate / Temperature Zone,
Land Use and Tenure Classification.

Stakeholders: USDA NRCS soil scientists, FSA farm records administrators,
ag lenders valuing farmland, carbon credit registries, precision ag platforms
doing field-level analytics, insurance underwriters setting premium zones.
Source: USDA NRCS Land Capability Classification, USDA ERS Agricultural
Resource Management Survey, USDA Plant Hardiness Zone Map. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_land import (
    AG_LAND_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_land,
)


class TestDetermineLevel:
    def test_capability_category_is_level_1(self):
        assert _determine_level("daln_cap") == 1

    def test_class_1_is_level_2(self):
        assert _determine_level("daln_cap_1") == 2

    def test_region_category_is_level_1(self):
        assert _determine_level("daln_region") == 1

    def test_corn_belt_is_level_2(self):
        assert _determine_level("daln_region_corn") == 2

    def test_soil_category_is_level_1(self):
        assert _determine_level("daln_soil") == 1


class TestDetermineParent:
    def test_cap_category_has_no_parent(self):
        assert _determine_parent("daln_cap") is None

    def test_class_1_parent_is_cap(self):
        assert _determine_parent("daln_cap_1") == "daln_cap"

    def test_corn_belt_parent_is_region(self):
        assert _determine_parent("daln_region_corn") == "daln_region"

    def test_clay_parent_is_soil(self):
        assert _determine_parent("daln_soil_clay") == "daln_soil"


class TestAgLandNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_LAND_NODES) > 0

    def test_has_land_capability_category(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_cap" in codes

    def test_has_region_category(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_region" in codes

    def test_has_soil_category(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_soil" in codes

    def test_has_water_category(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_water" in codes

    def test_has_climate_category(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_climate" in codes

    def test_has_class_1_node(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_cap_1" in codes

    def test_has_corn_belt_node(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert "daln_region_corn" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_LAND_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_LAND_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_LAND_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_LAND_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_LAND_NODES) >= 25

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_LAND_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_land_module_importable():
    assert callable(ingest_domain_ag_land)
    assert isinstance(AG_LAND_NODES, list)


def test_ingest_domain_ag_land(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_land(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_land'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_land'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_land_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_land(conn)
            count2 = await ingest_domain_ag_land(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
