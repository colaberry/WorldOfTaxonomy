"""Tests for Healthcare Payer and Reimbursement Model Types domain taxonomy ingester.

RED tests - written before any implementation exists.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_health_payer import (
    HEALTH_PAYER_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_health_payer,
)


class TestDetermineLevel:
    def test_medicare_category_is_level_1(self):
        assert _determine_level("dhspay_medicare") == 1

    def test_ffs_is_level_2(self):
        assert _determine_level("dhspay_medicare_ffs") == 2

    def test_medicaid_category_is_level_1(self):
        assert _determine_level("dhspay_medicaid") == 1


class TestDetermineParent:
    def test_medicare_has_no_parent(self):
        assert _determine_parent("dhspay_medicare") is None

    def test_ffs_parent_is_medicare(self):
        assert _determine_parent("dhspay_medicare_ffs") == "dhspay_medicare"

    def test_hmo_parent_is_medicaid(self):
        assert _determine_parent("dhspay_commercial_hmo") == "dhspay_commercial"


class TestNodes:
    def test_nodes_non_empty(self):
        assert len(HEALTH_PAYER_NODES) > 0

    def test_has_medicare_category(self):
        codes = [n[0] for n in HEALTH_PAYER_NODES]
        assert "dhspay_medicare" in codes

    def test_has_medicaid_category(self):
        codes = [n[0] for n in HEALTH_PAYER_NODES]
        assert "dhspay_medicaid" in codes

    def test_has_commercial_category(self):
        codes = [n[0] for n in HEALTH_PAYER_NODES]
        assert "dhspay_commercial" in codes

    def test_has_ffs_node(self):
        codes = [n[0] for n in HEALTH_PAYER_NODES]
        assert "dhspay_medicare_ffs" in codes

    def test_has_hmo_node(self):
        codes = [n[0] for n in HEALTH_PAYER_NODES]
        assert "dhspay_commercial_hmo" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in HEALTH_PAYER_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in HEALTH_PAYER_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in HEALTH_PAYER_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in HEALTH_PAYER_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(HEALTH_PAYER_NODES) >= 18

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in HEALTH_PAYER_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_module_importable():
    assert callable(ingest_domain_health_payer)
    assert isinstance(HEALTH_PAYER_NODES, list)


def test_ingest(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_health_payer(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_health_payer'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_health_payer(conn)
            count2 = await ingest_domain_health_payer(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
