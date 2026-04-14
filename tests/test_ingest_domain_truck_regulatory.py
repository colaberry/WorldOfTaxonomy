"""Tests for Truck Regulatory / Compliance Domains taxonomy ingester.

RED tests - written before any implementation exists.

Trucking Regulatory taxonomy classifies the regulatory compliance domains
that apply to truck operations - orthogonal to freight mode, vehicle class,
cargo type, and carrier ops:
  Hours of Service  (dtr_hos*)   - property, passenger, short-haul, ag exemptions
  Electronic Logging (dtr_eld*)  - mandate, exemptions, AOBRD legacy
  CDL / Licensing   (dtr_cdl*)   - Class A/B/C + endorsements (hazmat, tank, etc.)
  Hazmat Compliance (dtr_haz*)   - DOT 49 CFR, placards, training, security
  Emissions Standards (dtr_emiss*) - EPA, CARB, GHG phases, ZEV
  Food Safety Transport (dtr_food*) - FSMA, temperature control, traceability

Stakeholders: safety directors, compliance officers, DOT/FMCSA auditors,
insurance underwriters, fleet managers.
Source: 49 CFR Parts 390-399 (FMCSA), EPA 40 CFR, CARB ATCM. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_regulatory import (
    REGULATORY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_regulatory,
)


class TestDetermineLevel:
    def test_hos_category_is_level_1(self):
        assert _determine_level("dtr_hos") == 1

    def test_hos_property_is_level_2(self):
        assert _determine_level("dtr_hos_prop") == 2

    def test_eld_category_is_level_1(self):
        assert _determine_level("dtr_eld") == 1

    def test_eld_mandate_is_level_2(self):
        assert _determine_level("dtr_eld_mandate") == 2

    def test_cdl_category_is_level_1(self):
        assert _determine_level("dtr_cdl") == 1

    def test_cdl_class_a_is_level_2(self):
        assert _determine_level("dtr_cdl_class_a") == 2

    def test_emiss_category_is_level_1(self):
        assert _determine_level("dtr_emiss") == 1


class TestDetermineParent:
    def test_hos_category_has_no_parent(self):
        assert _determine_parent("dtr_hos") is None

    def test_hos_prop_parent_is_hos(self):
        assert _determine_parent("dtr_hos_prop") == "dtr_hos"

    def test_eld_mandate_parent_is_eld(self):
        assert _determine_parent("dtr_eld_mandate") == "dtr_eld"

    def test_cdl_class_a_parent_is_cdl(self):
        assert _determine_parent("dtr_cdl_class_a") == "dtr_cdl"

    def test_emiss_epa_parent_is_emiss(self):
        assert _determine_parent("dtr_emiss_epa") == "dtr_emiss"


class TestRegulatoryNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(REGULATORY_NODES) > 0

    def test_has_hos_category(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_hos" in codes

    def test_has_eld_category(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_eld" in codes

    def test_has_cdl_category(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_cdl" in codes

    def test_has_hazmat_category(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_haz" in codes

    def test_has_emissions_category(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_emiss" in codes

    def test_has_food_safety_category(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_food" in codes

    def test_has_cdl_class_a(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_cdl_class_a" in codes

    def test_has_hazmat_endorsement(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_cdl_haz" in codes

    def test_has_carb_emissions(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert "dtr_emiss_carb" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in REGULATORY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in REGULATORY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in REGULATORY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in REGULATORY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(REGULATORY_NODES) >= 25

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in REGULATORY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_truck_regulatory_module_importable():
    assert callable(ingest_domain_truck_regulatory)
    assert isinstance(REGULATORY_NODES, list)


def test_ingest_domain_truck_regulatory(db_pool):
    """Integration test: regulatory taxonomy rows + NAICS 484 links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_regulatory(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_regulatory'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_regulatory'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_regulatory_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_regulatory(conn)
            count2 = await ingest_domain_truck_regulatory(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
