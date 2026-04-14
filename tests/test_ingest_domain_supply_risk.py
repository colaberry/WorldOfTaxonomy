"""Tests for Supply Chain Risk and Disruption Category Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_supply_risk import (
    SUPPLY_RISK_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_supply_risk,
)


class TestDetermineLevel:
    def test_supplier_category_is_level_1(self):
        assert _determine_level("dscrisk_supplier") == 1

    def test_single_is_level_2(self):
        assert _determine_level("dscrisk_supplier_single") == 2

    def test_geo_category_is_level_1(self):
        assert _determine_level("dscrisk_geo") == 1


class TestDetermineParent:
    def test_supplier_has_no_parent(self):
        assert _determine_parent("dscrisk_supplier") is None

    def test_single_parent_is_supplier(self):
        assert _determine_parent("dscrisk_supplier_single") == "dscrisk_supplier"

    def test_trade_parent_is_geo(self):
        assert _determine_parent("dscrisk_geo_trade") == "dscrisk_geo"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(SUPPLY_RISK_NODES) > 0

    def test_has_supplier_category(self):
        codes = [n[0] for n in SUPPLY_RISK_NODES]
        assert "dscrisk_supplier" in codes

    def test_has_geo_category(self):
        codes = [n[0] for n in SUPPLY_RISK_NODES]
        assert "dscrisk_geo" in codes

    def test_has_weather_category(self):
        codes = [n[0] for n in SUPPLY_RISK_NODES]
        assert "dscrisk_weather" in codes

    def test_has_single_node(self):
        codes = [n[0] for n in SUPPLY_RISK_NODES]
        assert "dscrisk_supplier_single" in codes

    def test_has_trade_node(self):
        codes = [n[0] for n in SUPPLY_RISK_NODES]
        assert "dscrisk_geo_trade" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in SUPPLY_RISK_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in SUPPLY_RISK_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in SUPPLY_RISK_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in SUPPLY_RISK_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(SUPPLY_RISK_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in SUPPLY_RISK_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_supply_risk)
    assert isinstance(SUPPLY_RISK_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_supply_risk(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_supply_risk'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_supply_risk(conn)
            count2 = await ingest_domain_supply_risk(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
