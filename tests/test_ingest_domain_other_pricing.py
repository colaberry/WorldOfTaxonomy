"""Tests for Other Services Pricing and Business Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_other_pricing import (
    OTHER_PRICING_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_other_pricing,
)


class TestDetermineLevel:
    def test_perservice_category_is_level_1(self):
        assert _determine_level("dosprice_perservice") == 1

    def test_flat_is_level_2(self):
        assert _determine_level("dosprice_perservice_flat") == 2

    def test_subscription_category_is_level_1(self):
        assert _determine_level("dosprice_subscription") == 1


class TestDetermineParent:
    def test_perservice_has_no_parent(self):
        assert _determine_parent("dosprice_perservice") is None

    def test_flat_parent_is_perservice(self):
        assert _determine_parent("dosprice_perservice_flat") == "dosprice_perservice"

    def test_monthly_parent_is_subscription(self):
        assert _determine_parent("dosprice_subscription_monthly") == "dosprice_subscription"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(OTHER_PRICING_NODES) > 0

    def test_has_perservice_category(self):
        codes = [n[0] for n in OTHER_PRICING_NODES]
        assert "dosprice_perservice" in codes

    def test_has_subscription_category(self):
        codes = [n[0] for n in OTHER_PRICING_NODES]
        assert "dosprice_subscription" in codes

    def test_has_bundled_category(self):
        codes = [n[0] for n in OTHER_PRICING_NODES]
        assert "dosprice_bundled" in codes

    def test_has_flat_node(self):
        codes = [n[0] for n in OTHER_PRICING_NODES]
        assert "dosprice_perservice_flat" in codes

    def test_has_monthly_node(self):
        codes = [n[0] for n in OTHER_PRICING_NODES]
        assert "dosprice_subscription_monthly" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in OTHER_PRICING_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in OTHER_PRICING_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in OTHER_PRICING_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in OTHER_PRICING_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(OTHER_PRICING_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in OTHER_PRICING_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_other_pricing)
    assert isinstance(OTHER_PRICING_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_other_pricing(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_other_pricing'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_other_pricing(conn)
            count2 = await ingest_domain_other_pricing(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
