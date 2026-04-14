"""Tests for Agricultural Regulatory / Compliance Framework taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Regulatory taxonomy classifies compliance frameworks - orthogonal
to crop type, farming method, equipment, inputs, and market channel. The same
produce can be subject to USDA grading, FDA FSMA traceability, organic
certification, and GlobalGAP simultaneously, each managed by different
regulators, auditors, and buyers.

Code prefix: dagr_
Categories: USDA Commodity Program Compliance, FDA Food Safety (FSMA),
Organic and Sustainability Certification, Export / Phytosanitary,
Environmental Compliance, Labor and Worker Protection.

Stakeholders: compliance managers, export certifiers, organic certifiers,
food retailers requiring supplier certifications, crop insurance adjusters.
Source: USDA AMS/FSIS/FSA regulations, FDA FSMA rules, USDA NOP, APHIS PPQ
phytosanitary programs, EPA FIFRA. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_regulatory import (
    AG_REGULATORY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_regulatory,
)


class TestDetermineLevel:
    def test_usda_category_is_level_1(self):
        assert _determine_level("dagr_usda") == 1

    def test_fsa_program_is_level_2(self):
        assert _determine_level("dagr_usda_fsa") == 2

    def test_fsma_category_is_level_1(self):
        assert _determine_level("dagr_fsma") == 1

    def test_produce_safety_is_level_2(self):
        assert _determine_level("dagr_fsma_produce") == 2

    def test_organic_category_is_level_1(self):
        assert _determine_level("dagr_organic") == 1


class TestDetermineParent:
    def test_usda_category_has_no_parent(self):
        assert _determine_parent("dagr_usda") is None

    def test_fsa_parent_is_usda(self):
        assert _determine_parent("dagr_usda_fsa") == "dagr_usda"

    def test_produce_parent_is_fsma(self):
        assert _determine_parent("dagr_fsma_produce") == "dagr_fsma"

    def test_nop_parent_is_organic(self):
        assert _determine_parent("dagr_organic_nop") == "dagr_organic"


class TestAgRegulatoryNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_REGULATORY_NODES) > 0

    def test_has_usda_category(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_usda" in codes

    def test_has_fsma_category(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_fsma" in codes

    def test_has_organic_category(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_organic" in codes

    def test_has_export_phyto_category(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_export" in codes

    def test_has_environmental_category(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_env" in codes

    def test_has_nop_organic_node(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_organic_nop" in codes

    def test_has_fsma_produce_safety(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert "dagr_fsma_produce" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_REGULATORY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_REGULATORY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_REGULATORY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_REGULATORY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_REGULATORY_NODES) >= 25

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_REGULATORY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_regulatory_module_importable():
    assert callable(ingest_domain_ag_regulatory)
    assert isinstance(AG_REGULATORY_NODES, list)


def test_ingest_domain_ag_regulatory(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_regulatory(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_regulatory'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_regulatory'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_regulatory_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_regulatory(conn)
            count2 = await ingest_domain_ag_regulatory(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
