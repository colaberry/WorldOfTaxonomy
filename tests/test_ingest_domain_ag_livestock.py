"""Tests for Agriculture Livestock Category domain taxonomy ingester.

RED tests - written before any implementation exists.

Livestock taxonomy organizes animal agriculture into categories:
  Cattle    (dal_cattle*)  - beef, dairy
  Swine     (dal_swine*)   - market hogs, breeding stock
  Poultry   (dal_poultry*) - broilers, layers, turkeys
  Sheep/Goat (dal_small*)  - sheep, goats
  Equine    (dal_equine*)  - horses, mules
  Aqua      (dal_aqua*)    - fish, shellfish (aquaculture)
  Other     (dal_other*)   - bees, rabbits, specialty animals

Source: USDA NASS livestock categories. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_livestock import (
    LIVESTOCK_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_livestock,
)


class TestDetermineLevel:
    def test_cattle_category_is_level_1(self):
        assert _determine_level("dal_cattle") == 1

    def test_cattle_type_is_level_2(self):
        assert _determine_level("dal_cattle_beef") == 2

    def test_poultry_category_is_level_1(self):
        assert _determine_level("dal_poultry") == 1

    def test_poultry_type_is_level_2(self):
        assert _determine_level("dal_poultry_broiler") == 2


class TestDetermineParent:
    def test_cattle_category_has_no_parent(self):
        assert _determine_parent("dal_cattle") is None

    def test_beef_parent_is_cattle(self):
        assert _determine_parent("dal_cattle_beef") == "dal_cattle"

    def test_broiler_parent_is_poultry(self):
        assert _determine_parent("dal_poultry_broiler") == "dal_poultry"


class TestLivestockNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(LIVESTOCK_NODES) > 0

    def test_has_cattle_category(self):
        codes = [n[0] for n in LIVESTOCK_NODES]
        assert "dal_cattle" in codes

    def test_has_swine_category(self):
        codes = [n[0] for n in LIVESTOCK_NODES]
        assert "dal_swine" in codes

    def test_has_poultry_category(self):
        codes = [n[0] for n in LIVESTOCK_NODES]
        assert "dal_poultry" in codes

    def test_has_beef_cattle(self):
        codes = [n[0] for n in LIVESTOCK_NODES]
        assert "dal_cattle_beef" in codes

    def test_has_dairy_cattle(self):
        codes = [n[0] for n in LIVESTOCK_NODES]
        assert "dal_cattle_dairy" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in LIVESTOCK_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in LIVESTOCK_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in LIVESTOCK_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in LIVESTOCK_NODES:
            if level == 2:
                assert parent is not None


def test_domain_ag_livestock_module_importable():
    assert callable(ingest_domain_ag_livestock)
    assert isinstance(LIVESTOCK_NODES, list)


def test_ingest_domain_ag_livestock(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_livestock(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_livestock'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_livestock'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_livestock_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_livestock(conn)
            count2 = await ingest_domain_ag_livestock(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
