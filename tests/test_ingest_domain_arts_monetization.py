"""Tests for Arts and Entertainment Monetization and Distribution Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_arts_monetization import (
    ARTS_MONETIZATION_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_arts_monetization,
)


class TestDetermineLevel:
    def test_ticket_category_is_level_1(self):
        assert _determine_level("dacmon_ticket") == 1

    def test_live_is_level_2(self):
        assert _determine_level("dacmon_ticket_live") == 2

    def test_subscription_category_is_level_1(self):
        assert _determine_level("dacmon_subscription") == 1


class TestDetermineParent:
    def test_ticket_has_no_parent(self):
        assert _determine_parent("dacmon_ticket") is None

    def test_live_parent_is_ticket(self):
        assert _determine_parent("dacmon_ticket_live") == "dacmon_ticket"

    def test_svod_parent_is_subscription(self):
        assert _determine_parent("dacmon_subscription_svod") == "dacmon_subscription"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(ARTS_MONETIZATION_NODES) > 0

    def test_has_ticket_category(self):
        codes = [n[0] for n in ARTS_MONETIZATION_NODES]
        assert "dacmon_ticket" in codes

    def test_has_subscription_category(self):
        codes = [n[0] for n in ARTS_MONETIZATION_NODES]
        assert "dacmon_subscription" in codes

    def test_has_advertising_category(self):
        codes = [n[0] for n in ARTS_MONETIZATION_NODES]
        assert "dacmon_advertising" in codes

    def test_has_live_node(self):
        codes = [n[0] for n in ARTS_MONETIZATION_NODES]
        assert "dacmon_ticket_live" in codes

    def test_has_svod_node(self):
        codes = [n[0] for n in ARTS_MONETIZATION_NODES]
        assert "dacmon_subscription_svod" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in ARTS_MONETIZATION_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in ARTS_MONETIZATION_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in ARTS_MONETIZATION_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in ARTS_MONETIZATION_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(ARTS_MONETIZATION_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in ARTS_MONETIZATION_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_arts_monetization)
    assert isinstance(ARTS_MONETIZATION_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_arts_monetization(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_arts_monetization'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_arts_monetization(conn)
            count2 = await ingest_domain_arts_monetization(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
