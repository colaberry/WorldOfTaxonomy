"""Tests for Construction Sustainability and Green Building Certification domain taxonomy ingester.

RED tests - written before any implementation exists.

Construction Sustainability taxonomy classifies what environmental performance
certification and green building standard applies to a project - orthogonal
to trade type, building type, delivery method, and material. The same LEED
rating system certifies a wood-frame affordable housing project, a concrete
office tower, and a steel data center, all using different delivery methods
and trades.

Code prefix: dcss_
Categories: LEED and Green Building Rating Systems, Energy Performance
Certification, Embodied Carbon and Materials, Resilience and Climate
Adaptation, Green Financing and Incentive Programs.

Stakeholders: sustainability consultants, LEED APs, energy code officials
(ASHRAE 90.1), green bond issuers, ESG-focused real estate investors,
building owners seeking utility incentive rebates.
Source: USGBC LEED v4.1 rating system, ASHRAE 90.1 energy standard,
BREEAM standards, Passive House Institute PHI, IgCC. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_const_sustainability import (
    CONST_SUSTAINABILITY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_const_sustainability,
)


class TestDetermineLevel:
    def test_leed_category_is_level_1(self):
        assert _determine_level("dcss_leed") == 1

    def test_leed_bd_is_level_2(self):
        assert _determine_level("dcss_leed_bdnc") == 2

    def test_energy_category_is_level_1(self):
        assert _determine_level("dcss_energy") == 1

    def test_carbon_category_is_level_1(self):
        assert _determine_level("dcss_carbon") == 1

    def test_passive_house_is_level_2(self):
        assert _determine_level("dcss_energy_passive") == 2


class TestDetermineParent:
    def test_leed_category_has_no_parent(self):
        assert _determine_parent("dcss_leed") is None

    def test_bdnc_parent_is_leed(self):
        assert _determine_parent("dcss_leed_bdnc") == "dcss_leed"

    def test_passive_parent_is_energy(self):
        assert _determine_parent("dcss_energy_passive") == "dcss_energy"

    def test_lca_parent_is_carbon(self):
        assert _determine_parent("dcss_carbon_lca") == "dcss_carbon"


class TestConstSustainabilityNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(CONST_SUSTAINABILITY_NODES) > 0

    def test_has_leed_category(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert "dcss_leed" in codes

    def test_has_energy_category(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert "dcss_energy" in codes

    def test_has_carbon_category(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert "dcss_carbon" in codes

    def test_has_resilience_category(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert "dcss_resilience" in codes

    def test_has_leed_bdnc_node(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert "dcss_leed_bdnc" in codes

    def test_has_passive_house_node(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert "dcss_energy_passive" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in CONST_SUSTAINABILITY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in CONST_SUSTAINABILITY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in CONST_SUSTAINABILITY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in CONST_SUSTAINABILITY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(CONST_SUSTAINABILITY_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in CONST_SUSTAINABILITY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_const_sustainability_module_importable():
    assert callable(ingest_domain_const_sustainability)
    assert isinstance(CONST_SUSTAINABILITY_NODES, list)


def test_ingest_domain_const_sustainability(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_const_sustainability(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_const_sustainability'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_const_sustainability'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_const_sustainability_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_const_sustainability(conn)
            count2 = await ingest_domain_const_sustainability(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
