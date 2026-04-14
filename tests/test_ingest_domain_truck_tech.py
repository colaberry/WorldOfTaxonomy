"""Tests for Truck Technology / Digitization Level domain taxonomy ingester.

RED tests - written before any implementation exists.

Trucking Technology taxonomy classifies how freight is booked, managed,
tracked, and operated - orthogonal to freight mode, vehicle class, cargo
type, carrier ops, pricing, and regulatory domains:
  Load Booking/Matching (dtt_book*) - manual, load boards, digital freight, API
  TMS Maturity          (dtt_tms*)  - none, basic, full-suite, cloud, integrated
  Fleet Telematics      (dtt_telem*) - GPS, ELD telematics, dashcam, ADAS, asset
  Automation Level      (dtt_auto*) - none, ADAS, partial, platooning, AV
  Digital Documentation (dtt_doc*)  - paper, eBOL, ePOD, blockchain, EDI/API

Stakeholders: technology vendors, shippers evaluating carrier digital maturity,
investors assessing logistics tech adoption, fleet managers.
Source: FMCSA ELD data, DAT/Truckstop market data, ATA technology surveys. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_tech import (
    TECH_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_tech,
)


class TestDetermineLevel:
    def test_book_category_is_level_1(self):
        assert _determine_level("dtt_book") == 1

    def test_load_board_is_level_2(self):
        assert _determine_level("dtt_book_board") == 2

    def test_tms_category_is_level_1(self):
        assert _determine_level("dtt_tms") == 1

    def test_tms_cloud_is_level_2(self):
        assert _determine_level("dtt_tms_cloud") == 2

    def test_telem_category_is_level_1(self):
        assert _determine_level("dtt_telem") == 1

    def test_gps_is_level_2(self):
        assert _determine_level("dtt_telem_gps") == 2

    def test_auto_category_is_level_1(self):
        assert _determine_level("dtt_auto") == 1

    def test_doc_category_is_level_1(self):
        assert _determine_level("dtt_doc") == 1


class TestDetermineParent:
    def test_book_category_has_no_parent(self):
        assert _determine_parent("dtt_book") is None

    def test_book_board_parent_is_book(self):
        assert _determine_parent("dtt_book_board") == "dtt_book"

    def test_tms_cloud_parent_is_tms(self):
        assert _determine_parent("dtt_tms_cloud") == "dtt_tms"

    def test_telem_gps_parent_is_telem(self):
        assert _determine_parent("dtt_telem_gps") == "dtt_telem"

    def test_auto_av_parent_is_auto(self):
        assert _determine_parent("dtt_auto_av") == "dtt_auto"


class TestTechNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(TECH_NODES) > 0

    def test_has_booking_category(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_book" in codes

    def test_has_tms_category(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_tms" in codes

    def test_has_telematics_category(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_telem" in codes

    def test_has_automation_category(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_auto" in codes

    def test_has_digital_docs_category(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_doc" in codes

    def test_has_digital_freight_matching(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_book_dfm" in codes

    def test_has_gps_telematics(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_telem_gps" in codes

    def test_has_autonomous_vehicle(self):
        codes = [n[0] for n in TECH_NODES]
        assert "dtt_auto_av" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in TECH_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in TECH_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in TECH_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in TECH_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(TECH_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in TECH_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_truck_tech_module_importable():
    assert callable(ingest_domain_truck_tech)
    assert isinstance(TECH_NODES, list)


def test_ingest_domain_truck_tech(db_pool):
    """Integration test: tech taxonomy rows + NAICS 484 links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_tech(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_tech'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_tech'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_tech_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_tech(conn)
            count2 = await ingest_domain_truck_tech(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
