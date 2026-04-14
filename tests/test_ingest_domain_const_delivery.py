"""Tests for Construction Project Delivery Method domain taxonomy ingester.

RED tests - written before any implementation exists.

Construction Project Delivery taxonomy classifies HOW a construction project
is contracted and organized - orthogonal to trade type and building type.
The same office tower can be delivered via design-bid-build with the lowest
bidder, a design-build team, a CM at risk with GMP, or a public-private
partnership. The delivery method determines risk allocation, schedule,
cost certainty, and contractor selection.

Code prefix: dcpd_
Categories: Traditional Design-Bid-Build, Design-Build and Integrated
Delivery, Construction Management Models, Public-Private Partnership,
Specialty and Alternative Delivery.

Stakeholders: owners selecting delivery method, construction attorneys
drafting AIA/DBIA contracts, surety bond underwriters, public agency
procurement officers, project finance lenders evaluating risk allocation.
Source: AIA (American Institute of Architects) contract families, DBIA
(Design-Build Institute of America), CMAA (Construction Management
Association of America) standards. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_const_delivery import (
    CONST_DELIVERY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_const_delivery,
)


class TestDetermineLevel:
    def test_dbb_category_is_level_1(self):
        assert _determine_level("dcpd_dbb") == 1

    def test_low_bid_is_level_2(self):
        assert _determine_level("dcpd_dbb_lowbid") == 2

    def test_db_category_is_level_1(self):
        assert _determine_level("dcpd_db") == 1

    def test_bridging_is_level_2(self):
        assert _determine_level("dcpd_db_bridging") == 2

    def test_cm_category_is_level_1(self):
        assert _determine_level("dcpd_cm") == 1


class TestDetermineParent:
    def test_dbb_category_has_no_parent(self):
        assert _determine_parent("dcpd_dbb") is None

    def test_low_bid_parent_is_dbb(self):
        assert _determine_parent("dcpd_dbb_lowbid") == "dcpd_dbb"

    def test_bridging_parent_is_db(self):
        assert _determine_parent("dcpd_db_bridging") == "dcpd_db"

    def test_gmp_parent_is_cm(self):
        assert _determine_parent("dcpd_cm_gmp") == "dcpd_cm"


class TestConstDeliveryNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(CONST_DELIVERY_NODES) > 0

    def test_has_dbb_category(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert "dcpd_dbb" in codes

    def test_has_db_category(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert "dcpd_db" in codes

    def test_has_cm_category(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert "dcpd_cm" in codes

    def test_has_p3_category(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert "dcpd_p3" in codes

    def test_has_low_bid_node(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert "dcpd_dbb_lowbid" in codes

    def test_has_gmp_node(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert "dcpd_cm_gmp" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in CONST_DELIVERY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in CONST_DELIVERY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in CONST_DELIVERY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in CONST_DELIVERY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(CONST_DELIVERY_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in CONST_DELIVERY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_const_delivery_module_importable():
    assert callable(ingest_domain_const_delivery)
    assert isinstance(CONST_DELIVERY_NODES, list)


def test_ingest_domain_const_delivery(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_const_delivery(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_const_delivery'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_const_delivery'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_const_delivery_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_const_delivery(conn)
            count2 = await ingest_domain_const_delivery(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
