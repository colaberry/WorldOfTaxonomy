"""Tests for Utility Grid Region domain taxonomy ingester.

RED tests - written before any implementation exists.

Grid taxonomy organizes electrical grid infrastructure:
  Voltage Level (dug_voltage*) - transmission, sub-transmission, distribution, LV
  Grid Region   (dug_region*)  - NERC reliability regions (ERCOT, PJM, MISO, etc.)

Source: NERC (North American Electric Reliability Corporation). Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_util_grid import (
    GRID_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_util_grid,
)


class TestDetermineLevel:
    def test_voltage_category_is_level_1(self):
        assert _determine_level("dug_voltage") == 1

    def test_transmission_is_level_2(self):
        assert _determine_level("dug_voltage_trans") == 2

    def test_region_category_is_level_1(self):
        assert _determine_level("dug_region") == 1

    def test_ercot_is_level_2(self):
        assert _determine_level("dug_region_ercot") == 2


class TestDetermineParent:
    def test_voltage_category_has_no_parent(self):
        assert _determine_parent("dug_voltage") is None

    def test_transmission_parent_is_voltage(self):
        assert _determine_parent("dug_voltage_trans") == "dug_voltage"

    def test_ercot_parent_is_region(self):
        assert _determine_parent("dug_region_ercot") == "dug_region"


class TestGridNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(GRID_NODES) > 0

    def test_has_voltage_category(self):
        codes = [n[0] for n in GRID_NODES]
        assert "dug_voltage" in codes

    def test_has_region_category(self):
        codes = [n[0] for n in GRID_NODES]
        assert "dug_region" in codes

    def test_has_ercot(self):
        codes = [n[0] for n in GRID_NODES]
        assert "dug_region_ercot" in codes

    def test_has_pjm(self):
        codes = [n[0] for n in GRID_NODES]
        assert "dug_region_pjm" in codes

    def test_has_transmission_voltage(self):
        codes = [n[0] for n in GRID_NODES]
        assert "dug_voltage_trans" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in GRID_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in GRID_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in GRID_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in GRID_NODES:
            if level == 2:
                assert parent is not None


def test_domain_util_grid_module_importable():
    assert callable(ingest_domain_util_grid)
    assert isinstance(GRID_NODES, list)


def test_ingest_domain_util_grid(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_util_grid(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_util_grid'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_util_grid_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_util_grid(conn)
            count2 = await ingest_domain_util_grid(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
