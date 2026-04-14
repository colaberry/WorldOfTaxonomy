"""Tests for Agricultural Input Supply Types domain taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Input taxonomy classifies what goes INTO the farm as inputs -
orthogonal to crop type, livestock category, farming method, equipment, and
commodity grade. The same crop grown with the same equipment can use
conventional vs. organic inputs, GMO vs. heirloom seeds, synthetic vs.
biological pest control.

Code prefix: dai_ (ag input - note: distinct from domain_ai_data's dai_ prefix)

Wait - to avoid collision with domain_ai_data (dai_*), use prefix: daip_

Code prefix: daip_
Categories: Seed and Planting Material, Crop Protection Products, Fertilizers
and Soil Amendments, Animal Feed and Nutrition, Veterinary Products,
Energy and Fuel Inputs, Water and Irrigation Inputs.

Stakeholders: ag input manufacturers, seed companies, precision ag platforms,
USDA FSA program administrators, lenders calculating input cost financing.
Source: USDA ERS input use surveys, EPA pesticide registration data. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_input import (
    AG_INPUT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_input,
)


class TestDetermineLevel:
    def test_seed_category_is_level_1(self):
        assert _determine_level("daip_seed") == 1

    def test_gmo_seed_is_level_2(self):
        assert _determine_level("daip_seed_gmo") == 2

    def test_crop_protect_category_is_level_1(self):
        assert _determine_level("daip_protect") == 1

    def test_herbicide_is_level_2(self):
        assert _determine_level("daip_protect_herb") == 2

    def test_fert_category_is_level_1(self):
        assert _determine_level("daip_fert") == 1


class TestDetermineParent:
    def test_seed_category_has_no_parent(self):
        assert _determine_parent("daip_seed") is None

    def test_gmo_parent_is_seed(self):
        assert _determine_parent("daip_seed_gmo") == "daip_seed"

    def test_herbicide_parent_is_protect(self):
        assert _determine_parent("daip_protect_herb") == "daip_protect"

    def test_nitrogen_parent_is_fert(self):
        assert _determine_parent("daip_fert_n") == "daip_fert"


class TestAgInputNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_INPUT_NODES) > 0

    def test_has_seed_category(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_seed" in codes

    def test_has_crop_protection_category(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_protect" in codes

    def test_has_fertilizer_category(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_fert" in codes

    def test_has_animal_feed_category(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_feed" in codes

    def test_has_vet_products_category(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_vet" in codes

    def test_has_gmo_seed_node(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_seed_gmo" in codes

    def test_has_organic_seed_node(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_seed_organic" in codes

    def test_has_herbicide_node(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert "daip_protect_herb" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_INPUT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_INPUT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_INPUT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_INPUT_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_INPUT_NODES) >= 25

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_INPUT_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_input_module_importable():
    assert callable(ingest_domain_ag_input)
    assert isinstance(AG_INPUT_NODES, list)


def test_ingest_domain_ag_input(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_input(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_input'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_input'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_input_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_input(conn)
            count2 = await ingest_domain_ag_input(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
