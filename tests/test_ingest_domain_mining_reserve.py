"""Tests for Mining Reserve Classification domain taxonomy ingester.

RED tests - written before any implementation exists.

Reserve classification taxonomy uses SPE-PRMS (Petroleum Resources Management System):
  Reserves         (dmr_res*)   - proved (1P), probable (2P), possible (3P)
  Contingent       (dmr_cont*)  - 1C, 2C, 3C (discovered but not yet commercial)
  Prospective      (dmr_prosp*) - low, best, high estimate (undiscovered)

Source: Society of Petroleum Engineers (SPE) PRMS framework. Open standard.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mining_reserve import (
    RESERVE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mining_reserve,
)


class TestDetermineLevel:
    def test_reserves_category_is_level_1(self):
        assert _determine_level("dmr_res") == 1

    def test_proved_is_level_2(self):
        assert _determine_level("dmr_res_proved") == 2

    def test_contingent_category_is_level_1(self):
        assert _determine_level("dmr_cont") == 1

    def test_contingent_type_is_level_2(self):
        assert _determine_level("dmr_cont_2c") == 2


class TestDetermineParent:
    def test_reserves_category_has_no_parent(self):
        assert _determine_parent("dmr_res") is None

    def test_proved_parent_is_res(self):
        assert _determine_parent("dmr_res_proved") == "dmr_res"

    def test_contingent_2c_parent_is_cont(self):
        assert _determine_parent("dmr_cont_2c") == "dmr_cont"


class TestReserveNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(RESERVE_NODES) > 0

    def test_has_reserves_category(self):
        codes = [n[0] for n in RESERVE_NODES]
        assert "dmr_res" in codes

    def test_has_contingent_category(self):
        codes = [n[0] for n in RESERVE_NODES]
        assert "dmr_cont" in codes

    def test_has_prospective_category(self):
        codes = [n[0] for n in RESERVE_NODES]
        assert "dmr_prosp" in codes

    def test_has_proved_reserves(self):
        codes = [n[0] for n in RESERVE_NODES]
        assert "dmr_res_proved" in codes

    def test_has_probable_reserves(self):
        codes = [n[0] for n in RESERVE_NODES]
        assert "dmr_res_probable" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in RESERVE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in RESERVE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in RESERVE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in RESERVE_NODES:
            if level == 2:
                assert parent is not None


def test_domain_mining_reserve_module_importable():
    assert callable(ingest_domain_mining_reserve)
    assert isinstance(RESERVE_NODES, list)


def test_ingest_domain_mining_reserve(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mining_reserve(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mining_reserve'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mining_reserve_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mining_reserve(conn)
            count2 = await ingest_domain_mining_reserve(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
