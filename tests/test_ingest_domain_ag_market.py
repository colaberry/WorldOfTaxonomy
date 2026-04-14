"""Tests for Agricultural Market Channel / Sales Type domain taxonomy ingester.

RED tests - written before any implementation exists.

Agriculture Market Channel taxonomy classifies WHERE farm output is sold -
orthogonal to crop type, livestock, farming method, equipment, inputs, and
farm business structure. The same corn bushel from the same family farm
with the same equipment and inputs can go to a commodity elevator, a food
processor under contract, a cooperative pool, an export terminal, or a
distillery directly.

Code prefix: damt_
Categories: Commodity Market Channels, Contractual / Forward Sales,
Cooperative and Pooled Marketing, Direct and Local Market Channels,
Export and International Trade, Government and Program Channels.

Stakeholders: grain merchants, ag lenders calculating revenue streams,
farm managers timing sales, USDA AMS market news reporters, food companies
sourcing traceability.
Source: USDA AMS market data, CBOT/CME agricultural futures, USDA ERS
marketing margins. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_market import (
    AG_MARKET_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_market,
)


class TestDetermineLevel:
    def test_commodity_category_is_level_1(self):
        assert _determine_level("damt_commodity") == 1

    def test_spot_cash_is_level_2(self):
        assert _determine_level("damt_commodity_spot") == 2

    def test_contract_category_is_level_1(self):
        assert _determine_level("damt_contract") == 1

    def test_forward_is_level_2(self):
        assert _determine_level("damt_contract_forward") == 2

    def test_coop_category_is_level_1(self):
        assert _determine_level("damt_coop") == 1


class TestDetermineParent:
    def test_commodity_category_has_no_parent(self):
        assert _determine_parent("damt_commodity") is None

    def test_spot_parent_is_commodity(self):
        assert _determine_parent("damt_commodity_spot") == "damt_commodity"

    def test_forward_parent_is_contract(self):
        assert _determine_parent("damt_contract_forward") == "damt_contract"

    def test_export_bulk_parent_is_export(self):
        assert _determine_parent("damt_export_bulk") == "damt_export"


class TestAgMarketNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(AG_MARKET_NODES) > 0

    def test_has_commodity_channel(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_commodity" in codes

    def test_has_contract_channel(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_contract" in codes

    def test_has_coop_channel(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_coop" in codes

    def test_has_direct_channel(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_direct" in codes

    def test_has_export_channel(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_export" in codes

    def test_has_spot_cash_node(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_commodity_spot" in codes

    def test_has_forward_contract_node(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert "damt_contract_forward" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in AG_MARKET_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in AG_MARKET_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in AG_MARKET_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in AG_MARKET_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(AG_MARKET_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in AG_MARKET_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_ag_market_module_importable():
    assert callable(ingest_domain_ag_market)
    assert isinstance(AG_MARKET_NODES, list)


def test_ingest_domain_ag_market(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_market(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_market'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_ag_market'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_market_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_market(conn)
            count2 = await ingest_domain_ag_market(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
