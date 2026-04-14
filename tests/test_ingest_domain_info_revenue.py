"""Tests for Information and Media Revenue and Monetization Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_info_revenue import (
    INFO_REVENUE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_info_revenue,
)


class TestDetermineLevel:
    def test_subscription_category_is_level_1(self):
        assert _determine_level("dimrev_subscription") == 1

    def test_svod_is_level_2(self):
        assert _determine_level("dimrev_subscription_svod") == 2

    def test_advertising_category_is_level_1(self):
        assert _determine_level("dimrev_advertising") == 1


class TestDetermineParent:
    def test_subscription_has_no_parent(self):
        assert _determine_parent("dimrev_subscription") is None

    def test_svod_parent_is_subscription(self):
        assert _determine_parent("dimrev_subscription_svod") == "dimrev_subscription"

    def test_programmatic_parent_is_advertising(self):
        assert _determine_parent("dimrev_advertising_programmatic") == "dimrev_advertising"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(INFO_REVENUE_NODES) > 0

    def test_has_subscription_category(self):
        codes = [n[0] for n in INFO_REVENUE_NODES]
        assert "dimrev_subscription" in codes

    def test_has_advertising_category(self):
        codes = [n[0] for n in INFO_REVENUE_NODES]
        assert "dimrev_advertising" in codes

    def test_has_transactional_category(self):
        codes = [n[0] for n in INFO_REVENUE_NODES]
        assert "dimrev_transactional" in codes

    def test_has_svod_node(self):
        codes = [n[0] for n in INFO_REVENUE_NODES]
        assert "dimrev_subscription_svod" in codes

    def test_has_programmatic_node(self):
        codes = [n[0] for n in INFO_REVENUE_NODES]
        assert "dimrev_advertising_programmatic" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in INFO_REVENUE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in INFO_REVENUE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in INFO_REVENUE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in INFO_REVENUE_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(INFO_REVENUE_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in INFO_REVENUE_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_info_revenue)
    assert isinstance(INFO_REVENUE_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_info_revenue(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_info_revenue'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_info_revenue(conn)
            count2 = await ingest_domain_info_revenue(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
