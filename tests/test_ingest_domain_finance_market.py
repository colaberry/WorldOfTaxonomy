"""Tests for Finance Market and Exchange Structure Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_finance_market import (
    FINANCE_MARKET_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_finance_market,
)


class TestDetermineLevel:
    def test_exchange_category_is_level_1(self):
        assert _determine_level("dfimkt_exchange") == 1

    def test_nyse_is_level_2(self):
        assert _determine_level("dfimkt_exchange_nyse") == 2

    def test_otc_category_is_level_1(self):
        assert _determine_level("dfimkt_otc") == 1


class TestDetermineParent:
    def test_exchange_has_no_parent(self):
        assert _determine_parent("dfimkt_exchange") is None

    def test_nyse_parent_is_exchange(self):
        assert _determine_parent("dfimkt_exchange_nyse") == "dfimkt_exchange"

    def test_dealer_parent_is_otc(self):
        assert _determine_parent("dfimkt_otc_dealer") == "dfimkt_otc"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(FINANCE_MARKET_NODES) > 0

    def test_has_exchange_category(self):
        codes = [n[0] for n in FINANCE_MARKET_NODES]
        assert "dfimkt_exchange" in codes

    def test_has_otc_category(self):
        codes = [n[0] for n in FINANCE_MARKET_NODES]
        assert "dfimkt_otc" in codes

    def test_has_private_category(self):
        codes = [n[0] for n in FINANCE_MARKET_NODES]
        assert "dfimkt_private" in codes

    def test_has_nyse_node(self):
        codes = [n[0] for n in FINANCE_MARKET_NODES]
        assert "dfimkt_exchange_nyse" in codes

    def test_has_dealer_node(self):
        codes = [n[0] for n in FINANCE_MARKET_NODES]
        assert "dfimkt_otc_dealer" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in FINANCE_MARKET_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in FINANCE_MARKET_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in FINANCE_MARKET_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in FINANCE_MARKET_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(FINANCE_MARKET_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in FINANCE_MARKET_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_finance_market)
    assert isinstance(FINANCE_MARKET_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_finance_market(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_finance_market'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_finance_market(conn)
            count2 = await ingest_domain_finance_market(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
