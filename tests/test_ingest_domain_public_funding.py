"""Tests for Public Administration Funding Mechanism Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_public_funding import (
    PUBLIC_FUNDING_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_public_funding,
)


class TestDetermineLevel:
    def test_approp_category_is_level_1(self):
        assert _determine_level("dpafund_approp") == 1

    def test_annual_is_level_2(self):
        assert _determine_level("dpafund_approp_annual") == 2

    def test_fees_category_is_level_1(self):
        assert _determine_level("dpafund_fees") == 1


class TestDetermineParent:
    def test_approp_has_no_parent(self):
        assert _determine_parent("dpafund_approp") is None

    def test_annual_parent_is_approp(self):
        assert _determine_parent("dpafund_approp_annual") == "dpafund_approp"

    def test_federal_parent_is_fees(self):
        assert _determine_parent("dpafund_grants_federal") == "dpafund_grants"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(PUBLIC_FUNDING_NODES) > 0

    def test_has_approp_category(self):
        codes = [n[0] for n in PUBLIC_FUNDING_NODES]
        assert "dpafund_approp" in codes

    def test_has_fees_category(self):
        codes = [n[0] for n in PUBLIC_FUNDING_NODES]
        assert "dpafund_fees" in codes

    def test_has_grants_category(self):
        codes = [n[0] for n in PUBLIC_FUNDING_NODES]
        assert "dpafund_grants" in codes

    def test_has_annual_node(self):
        codes = [n[0] for n in PUBLIC_FUNDING_NODES]
        assert "dpafund_approp_annual" in codes

    def test_has_federal_node(self):
        codes = [n[0] for n in PUBLIC_FUNDING_NODES]
        assert "dpafund_grants_federal" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in PUBLIC_FUNDING_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in PUBLIC_FUNDING_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in PUBLIC_FUNDING_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in PUBLIC_FUNDING_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(PUBLIC_FUNDING_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in PUBLIC_FUNDING_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_public_funding)
    assert isinstance(PUBLIC_FUNDING_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_public_funding(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_public_funding'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_public_funding(conn)
            count2 = await ingest_domain_public_funding(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
