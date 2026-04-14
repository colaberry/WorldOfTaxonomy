"""Tests for Utility Infrastructure Asset Types domain taxonomy ingester.

RED tests - written before any implementation exists.

Utility Infrastructure Asset taxonomy classifies the physical capital assets
that utilities own and operate - orthogonal to energy source and grid region.
A gas-fired peaker plant, a wind farm, and a hydroelectric dam all involve
the same transmission line asset types; a coal plant and a solar farm both
connect through the same distribution transformer and substation equipment.

Code prefix: duia_
Categories: Generation Assets, Transmission Infrastructure, Distribution
Infrastructure, Customer Metering and Interface, Storage and Flexibility
Assets.

Stakeholders: utility asset managers, FERC AFUDC capital tracking, state PUC
rate base proceedings, utility M&A due diligence teams, grid reliability
planners (NERC TPL standards), insurance underwriters.
Source: FERC USOA (Uniform System of Accounts) plant accounts, NERC transmission
planning standards, IEEE distribution equipment standards. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_util_asset import (
    UTIL_ASSET_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_util_asset,
)


class TestDetermineLevel:
    def test_generation_category_is_level_1(self):
        assert _determine_level("duia_gen") == 1

    def test_plant_equipment_is_level_2(self):
        assert _determine_level("duia_gen_plant") == 2

    def test_transmission_category_is_level_1(self):
        assert _determine_level("duia_trans") == 1

    def test_distribution_category_is_level_1(self):
        assert _determine_level("duia_dist") == 1

    def test_substation_is_level_2(self):
        assert _determine_level("duia_trans_sub") == 2


class TestDetermineParent:
    def test_gen_category_has_no_parent(self):
        assert _determine_parent("duia_gen") is None

    def test_plant_parent_is_gen(self):
        assert _determine_parent("duia_gen_plant") == "duia_gen"

    def test_substation_parent_is_trans(self):
        assert _determine_parent("duia_trans_sub") == "duia_trans"

    def test_transformer_parent_is_dist(self):
        assert _determine_parent("duia_dist_xfmr") == "duia_dist"


class TestUtilAssetNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(UTIL_ASSET_NODES) > 0

    def test_has_generation_category(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert "duia_gen" in codes

    def test_has_transmission_category(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert "duia_trans" in codes

    def test_has_distribution_category(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert "duia_dist" in codes

    def test_has_metering_category(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert "duia_meter" in codes

    def test_has_substation_node(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert "duia_trans_sub" in codes

    def test_has_transformer_node(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert "duia_dist_xfmr" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in UTIL_ASSET_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in UTIL_ASSET_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in UTIL_ASSET_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in UTIL_ASSET_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(UTIL_ASSET_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in UTIL_ASSET_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_util_asset_module_importable():
    assert callable(ingest_domain_util_asset)
    assert isinstance(UTIL_ASSET_NODES, list)


def test_ingest_domain_util_asset(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_util_asset(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_util_asset'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_util_asset'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_util_asset_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_util_asset(conn)
            count2 = await ingest_domain_util_asset(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
