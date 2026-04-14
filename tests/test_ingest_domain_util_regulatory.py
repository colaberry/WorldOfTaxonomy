"""Tests for Utility Regulatory Framework domain taxonomy ingester.

RED tests - written before any implementation exists.

Utility Regulatory Framework taxonomy classifies what regulatory regime
governs a utility - orthogonal to energy source, grid region, tariff
structure, and asset type. An investor-owned utility (IOU) serving the
same load that a rural electric cooperative or a municipal utility serves
operates under completely different regulatory frameworks, ratemaking
processes, and ownership structures.

Code prefix: dureg_
Categories: Ownership and Utility Type, Federal Regulatory Jurisdiction,
State and Provincial Regulation, Market Structure and Competition,
Environmental Regulation.

Stakeholders: utility regulatory attorneys, state PUC commissioners, FERC
staff, rural electric cooperative (REC) directors, municipal utility managers,
energy policy analysts.
Source: FERC jurisdiction statutes (FPA, NGA), NARUC state commission
classifications, NRECA cooperative utility standards, EIA Form 861. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_util_regulatory import (
    UTIL_REGULATORY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_util_regulatory,
)


class TestDetermineLevel:
    def test_ownership_category_is_level_1(self):
        assert _determine_level("dureg_own") == 1

    def test_iou_is_level_2(self):
        assert _determine_level("dureg_own_iou") == 2

    def test_federal_category_is_level_1(self):
        assert _determine_level("dureg_federal") == 1

    def test_ferc_elec_is_level_2(self):
        assert _determine_level("dureg_federal_ferc") == 2

    def test_state_category_is_level_1(self):
        assert _determine_level("dureg_state") == 1


class TestDetermineParent:
    def test_own_category_has_no_parent(self):
        assert _determine_parent("dureg_own") is None

    def test_iou_parent_is_own(self):
        assert _determine_parent("dureg_own_iou") == "dureg_own"

    def test_ferc_parent_is_federal(self):
        assert _determine_parent("dureg_federal_ferc") == "dureg_federal"

    def test_puc_parent_is_state(self):
        assert _determine_parent("dureg_state_puc") == "dureg_state"


class TestUtilRegulatoryNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(UTIL_REGULATORY_NODES) > 0

    def test_has_ownership_category(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert "dureg_own" in codes

    def test_has_federal_category(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert "dureg_federal" in codes

    def test_has_state_category(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert "dureg_state" in codes

    def test_has_market_category(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert "dureg_market" in codes

    def test_has_iou_node(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert "dureg_own_iou" in codes

    def test_has_ferc_node(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert "dureg_federal_ferc" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in UTIL_REGULATORY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in UTIL_REGULATORY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in UTIL_REGULATORY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in UTIL_REGULATORY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(UTIL_REGULATORY_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in UTIL_REGULATORY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_util_regulatory_module_importable():
    assert callable(ingest_domain_util_regulatory)
    assert isinstance(UTIL_REGULATORY_NODES, list)


def test_ingest_domain_util_regulatory(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_util_regulatory(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_util_regulatory'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_util_regulatory'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_util_regulatory_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_util_regulatory(conn)
            count2 = await ingest_domain_util_regulatory(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
