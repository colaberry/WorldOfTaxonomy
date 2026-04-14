"""Tests for Agricultural Farm Business Structure domain taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Business Structure taxonomy classifies WHO owns and operates the
farm - orthogonal to what crops are grown, what animals are raised, what
equipment is used, and what inputs are applied. The same corn acre can be
operated by a 4th-generation family farm, a REIT-owned corporate farm,
an agricultural cooperative, or a contract grower tied to a food processor.

Code prefix: dab_
Categories: Farm Ownership Type, Farm Size and Scale, Business/Legal
Structure, Integration and Contracting Model, Capital and Financing Type.

Stakeholders: USDA Census of Agriculture, FSA program eligibility officers,
ag lenders (FCS, USDA RBCS), private equity ag investors, food processors
managing contract grower networks.
Source: USDA NASS Census of Agriculture, USDA ERS farm typology. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_business import (
    AG_BUSINESS_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_business,
)


class TestDetermineLevel:
    def test_ownership_category_is_level_1(self):
        assert _determine_level("dab_own") == 1

    def test_family_farm_is_level_2(self):
        assert _determine_level("dab_own_family") == 2

    def test_size_category_is_level_1(self):
        assert _determine_level("dab_size") == 1

    def test_small_farm_is_level_2(self):
        assert _determine_level("dab_size_small") == 2

    def test_structure_category_is_level_1(self):
        assert _determine_level("dab_structure") == 1


class TestDetermineParent:
    def test_ownership_category_has_no_parent(self):
        assert _determine_parent("dab_own") is None

    def test_family_parent_is_own(self):
        assert _determine_parent("dab_own_family") == "dab_own"

    def test_small_parent_is_size(self):
        assert _determine_parent("dab_size_small") == "dab_size"

    def test_contract_parent_is_contract(self):
        assert _determine_parent("dab_contract_grower") == "dab_contract"


class TestAgBusinessNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_BUSINESS_NODES) > 0

    def test_has_ownership_category(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_own" in codes

    def test_has_size_category(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_size" in codes

    def test_has_structure_category(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_structure" in codes

    def test_has_contract_category(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_contract" in codes

    def test_has_family_farm_node(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_own_family" in codes

    def test_has_cooperative_node(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_own_coop" in codes

    def test_has_corporate_farm_node(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert "dab_own_corporate" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_BUSINESS_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_BUSINESS_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_BUSINESS_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_BUSINESS_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_BUSINESS_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_BUSINESS_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_business_module_importable():
    assert callable(ingest_domain_ag_business)
    assert isinstance(AG_BUSINESS_NODES, list)


def test_ingest_domain_ag_business(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_business(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_business'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_business'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_business_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_business(conn)
            count2 = await ingest_domain_ag_business(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
