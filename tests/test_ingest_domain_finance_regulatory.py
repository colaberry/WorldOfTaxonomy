"""Tests for Finance Regulatory Framework Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_finance_regulatory import (
    FINANCE_REGULATORY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_finance_regulatory,
)


class TestDetermineLevel:
    def test_sec_category_is_level_1(self):
        assert _determine_level("dfireg_sec") == 1

    def test_broker_is_level_2(self):
        assert _determine_level("dfireg_sec_broker") == 2

    def test_cftc_category_is_level_1(self):
        assert _determine_level("dfireg_cftc") == 1


class TestDetermineParent:
    def test_sec_has_no_parent(self):
        assert _determine_parent("dfireg_sec") is None

    def test_broker_parent_is_sec(self):
        assert _determine_parent("dfireg_sec_broker") == "dfireg_sec"

    def test_futures_parent_is_cftc(self):
        assert _determine_parent("dfireg_cftc_futures") == "dfireg_cftc"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(FINANCE_REGULATORY_NODES) > 0

    def test_has_sec_category(self):
        codes = [n[0] for n in FINANCE_REGULATORY_NODES]
        assert "dfireg_sec" in codes

    def test_has_cftc_category(self):
        codes = [n[0] for n in FINANCE_REGULATORY_NODES]
        assert "dfireg_cftc" in codes

    def test_has_banking_category(self):
        codes = [n[0] for n in FINANCE_REGULATORY_NODES]
        assert "dfireg_banking" in codes

    def test_has_broker_node(self):
        codes = [n[0] for n in FINANCE_REGULATORY_NODES]
        assert "dfireg_sec_broker" in codes

    def test_has_futures_node(self):
        codes = [n[0] for n in FINANCE_REGULATORY_NODES]
        assert "dfireg_cftc_futures" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in FINANCE_REGULATORY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in FINANCE_REGULATORY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in FINANCE_REGULATORY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in FINANCE_REGULATORY_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(FINANCE_REGULATORY_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in FINANCE_REGULATORY_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_finance_regulatory)
    assert isinstance(FINANCE_REGULATORY_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_finance_regulatory(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_finance_regulatory'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_finance_regulatory(conn)
            count2 = await ingest_domain_finance_regulatory(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
