"""Tests for Mining Safety and Regulatory Compliance domain taxonomy ingester.

RED tests - written before any implementation exists.

Mining Safety taxonomy classifies compliance frameworks - orthogonal to
mineral type, extraction method, reserve classification, equipment, and
lifecycle phase. A surface gold mine and an underground coal mine both
face MSHA jurisdiction but under completely different parts of 30 CFR,
with different ventilation, blasting, and ground control requirements.

Code prefix: dmsaf_
Categories: MSHA Regulatory Domain (US federal), Environmental and Water
Compliance, Tailings and Waste Management, International Safety Standards,
Community and Social License.

Stakeholders: mine safety officers, MSHA district offices, mine inspectors,
environmental compliance managers, ESG-focused investors tracking incident
rates, government bond administrators requiring reclamation assurance.
Source: MSHA 30 CFR Parts 46-100 (surface) and Parts 56-57 (underground),
EPA hard rock mining regulations, MAC Towards Sustainable Mining (TSM),
ICMM Mining Principles. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mining_safety import (
    MINING_SAFETY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mining_safety,
)


class TestDetermineLevel:
    def test_msha_category_is_level_1(self):
        assert _determine_level("dmsaf_msha") == 1

    def test_surface_regs_is_level_2(self):
        assert _determine_level("dmsaf_msha_surface") == 2

    def test_env_category_is_level_1(self):
        assert _determine_level("dmsaf_env") == 1

    def test_tailings_category_is_level_1(self):
        assert _determine_level("dmsaf_tailings") == 1

    def test_water_permit_is_level_2(self):
        assert _determine_level("dmsaf_env_water") == 2


class TestDetermineParent:
    def test_msha_category_has_no_parent(self):
        assert _determine_parent("dmsaf_msha") is None

    def test_surface_parent_is_msha(self):
        assert _determine_parent("dmsaf_msha_surface") == "dmsaf_msha"

    def test_water_parent_is_env(self):
        assert _determine_parent("dmsaf_env_water") == "dmsaf_env"

    def test_tailing_dam_parent_is_tailings(self):
        assert _determine_parent("dmsaf_tailings_dam") == "dmsaf_tailings"


class TestMiningSafetyNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(MINING_SAFETY_NODES) > 0

    def test_has_msha_category(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert "dmsaf_msha" in codes

    def test_has_env_category(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert "dmsaf_env" in codes

    def test_has_tailings_category(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert "dmsaf_tailings" in codes

    def test_has_international_category(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert "dmsaf_intl" in codes

    def test_has_msha_surface_node(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert "dmsaf_msha_surface" in codes

    def test_has_tailings_dam_node(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert "dmsaf_tailings_dam" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MINING_SAFETY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MINING_SAFETY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MINING_SAFETY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MINING_SAFETY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(MINING_SAFETY_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in MINING_SAFETY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_mining_safety_module_importable():
    assert callable(ingest_domain_mining_safety)
    assert isinstance(MINING_SAFETY_NODES, list)


def test_ingest_domain_mining_safety(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mining_safety(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mining_safety'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_mining_safety'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mining_safety_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mining_safety(conn)
            count2 = await ingest_domain_mining_safety(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
