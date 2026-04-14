"""Tests for Real Estate Capital Structure and Ownership Vehicle Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_realestate_capital import (
    RE_CAPITAL_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_realestate_capital,
)


class TestDetermineLevel:
    def test_reit_category_is_level_1(self):
        assert _determine_level("drtcap_reit") == 1

    def test_equity_is_level_2(self):
        assert _determine_level("drtcap_reit_equity") == 2

    def test_fund_category_is_level_1(self):
        assert _determine_level("drtcap_fund") == 1


class TestDetermineParent:
    def test_reit_has_no_parent(self):
        assert _determine_parent("drtcap_reit") is None

    def test_equity_parent_is_reit(self):
        assert _determine_parent("drtcap_reit_equity") == "drtcap_reit"

    def test_closedend_parent_is_fund(self):
        assert _determine_parent("drtcap_fund_closedend") == "drtcap_fund"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(RE_CAPITAL_NODES) > 0

    def test_has_reit_category(self):
        codes = [n[0] for n in RE_CAPITAL_NODES]
        assert "drtcap_reit" in codes

    def test_has_fund_category(self):
        codes = [n[0] for n in RE_CAPITAL_NODES]
        assert "drtcap_fund" in codes

    def test_has_syndication_category(self):
        codes = [n[0] for n in RE_CAPITAL_NODES]
        assert "drtcap_syndication" in codes

    def test_has_equity_node(self):
        codes = [n[0] for n in RE_CAPITAL_NODES]
        assert "drtcap_reit_equity" in codes

    def test_has_closedend_node(self):
        codes = [n[0] for n in RE_CAPITAL_NODES]
        assert "drtcap_fund_closedend" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in RE_CAPITAL_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in RE_CAPITAL_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in RE_CAPITAL_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in RE_CAPITAL_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(RE_CAPITAL_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in RE_CAPITAL_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_realestate_capital)
    assert isinstance(RE_CAPITAL_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_realestate_capital(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_realestate_capital'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_realestate_capital(conn)
            count2 = await ingest_domain_realestate_capital(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
