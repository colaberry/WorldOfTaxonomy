"""Tests for Utility Tariff and Rate Structure domain taxonomy ingester.

RED tests - written before any implementation exists.

Utility Tariff taxonomy classifies how utilities price electricity and gas
delivery - orthogonal to energy source and grid region. The same kWh of
solar generation can be billed under a residential flat rate, a TOU rate,
a demand charge tariff for commercial customers, a wholesale LMP rate for
large industrials, or a net metering credit for distributed generation.

Code prefix: dut_
Categories: Residential Rate Structures, Commercial and Industrial Tariffs,
Wholesale and Market-Based Rates, Distributed Generation and Net Metering,
Special Purpose Tariffs.

Stakeholders: utility rate case analysts, PUC commissioners, large industrial
rate negotiators, solar project developers calculating net metering value,
demand response aggregators.
Source: FERC electric tariff filings, NARUC rate design guidelines, NREL
utility tariff database, EIA electric power survey. Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_util_tariff import (
    UTIL_TARIFF_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_util_tariff,
)


class TestDetermineLevel:
    def test_residential_category_is_level_1(self):
        assert _determine_level("dut_res") == 1

    def test_flat_rate_is_level_2(self):
        assert _determine_level("dut_res_flat") == 2

    def test_commercial_category_is_level_1(self):
        assert _determine_level("dut_comm") == 1

    def test_demand_charge_is_level_2(self):
        assert _determine_level("dut_comm_demand") == 2

    def test_wholesale_category_is_level_1(self):
        assert _determine_level("dut_wholesale") == 1


class TestDetermineParent:
    def test_res_category_has_no_parent(self):
        assert _determine_parent("dut_res") is None

    def test_flat_parent_is_res(self):
        assert _determine_parent("dut_res_flat") == "dut_res"

    def test_demand_parent_is_comm(self):
        assert _determine_parent("dut_comm_demand") == "dut_comm"

    def test_lmp_parent_is_wholesale(self):
        assert _determine_parent("dut_wholesale_lmp") == "dut_wholesale"


class TestUtilTariffNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(UTIL_TARIFF_NODES) > 0

    def test_has_residential_category(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert "dut_res" in codes

    def test_has_commercial_category(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert "dut_comm" in codes

    def test_has_wholesale_category(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert "dut_wholesale" in codes

    def test_has_nem_category(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert "dut_nem" in codes

    def test_has_flat_rate_node(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert "dut_res_flat" in codes

    def test_has_demand_charge_node(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert "dut_comm_demand" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in UTIL_TARIFF_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in UTIL_TARIFF_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in UTIL_TARIFF_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in UTIL_TARIFF_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(UTIL_TARIFF_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in UTIL_TARIFF_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_util_tariff_module_importable():
    assert callable(ingest_domain_util_tariff)
    assert isinstance(UTIL_TARIFF_NODES, list)


def test_ingest_domain_util_tariff(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_util_tariff(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_util_tariff'"
            )
            assert row is not None
            assert row["code_count"] == count
            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_util_tariff'"
            )
            assert link_count > 0
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_util_tariff_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_util_tariff(conn)
            count2 = await ingest_domain_util_tariff(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
