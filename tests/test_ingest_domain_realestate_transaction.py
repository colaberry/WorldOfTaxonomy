"""Tests for Real Estate Transaction Type Classification domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_realestate_transaction import (
    RE_TRANSACTION_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_realestate_transaction,
)


class TestDetermineLevel:
    def test_acquire_category_is_level_1(self):
        assert _determine_level("drttxn_acquire") == 1

    def test_core_is_level_2(self):
        assert _determine_level("drttxn_acquire_core") == 2

    def test_develop_category_is_level_1(self):
        assert _determine_level("drttxn_develop") == 1


class TestDetermineParent:
    def test_acquire_has_no_parent(self):
        assert _determine_parent("drttxn_acquire") is None

    def test_core_parent_is_acquire(self):
        assert _determine_parent("drttxn_acquire_core") == "drttxn_acquire"

    def test_ground_parent_is_develop(self):
        assert _determine_parent("drttxn_develop_ground") == "drttxn_develop"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(RE_TRANSACTION_NODES) > 0

    def test_has_acquire_category(self):
        codes = [n[0] for n in RE_TRANSACTION_NODES]
        assert "drttxn_acquire" in codes

    def test_has_develop_category(self):
        codes = [n[0] for n in RE_TRANSACTION_NODES]
        assert "drttxn_develop" in codes

    def test_has_finance_category(self):
        codes = [n[0] for n in RE_TRANSACTION_NODES]
        assert "drttxn_finance" in codes

    def test_has_core_node(self):
        codes = [n[0] for n in RE_TRANSACTION_NODES]
        assert "drttxn_acquire_core" in codes

    def test_has_ground_node(self):
        codes = [n[0] for n in RE_TRANSACTION_NODES]
        assert "drttxn_develop_ground" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in RE_TRANSACTION_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in RE_TRANSACTION_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in RE_TRANSACTION_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in RE_TRANSACTION_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(RE_TRANSACTION_NODES) >= 15

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in RE_TRANSACTION_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_realestate_transaction)
    assert isinstance(RE_TRANSACTION_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_realestate_transaction(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_realestate_transaction'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_realestate_transaction(conn)
            count2 = await ingest_domain_realestate_transaction(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
