"""Tests for Mining Mineral Types domain taxonomy ingester.

RED tests - written before any implementation exists.

Mineral taxonomy organizes extractable resources into categories:
  Metal Minerals      (dmm_metal*)   - iron, copper, gold, silver, aluminum
  Energy Minerals     (dmm_energy*)  - coal, oil, natural gas, uranium
  Industrial Minerals (dmm_indmin*)  - potash, limestone, silica, salt
  Construction Minerals (dmm_constr*) - aggregates, clay, gypsum
  Gemstones           (dmm_gem*)     - diamonds, colored gems

Source: USGS Mineral Resources Program + SPE classifications. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mining_mineral import (
    MINERAL_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mining_mineral,
)


class TestDetermineLevel:
    def test_metal_category_is_level_1(self):
        assert _determine_level("dmm_metal") == 1

    def test_metal_type_is_level_2(self):
        assert _determine_level("dmm_metal_au") == 2

    def test_energy_category_is_level_1(self):
        assert _determine_level("dmm_energy") == 1

    def test_energy_type_is_level_2(self):
        assert _determine_level("dmm_energy_coal") == 2


class TestDetermineParent:
    def test_metal_category_has_no_parent(self):
        assert _determine_parent("dmm_metal") is None

    def test_gold_parent_is_metal(self):
        assert _determine_parent("dmm_metal_au") == "dmm_metal"

    def test_coal_parent_is_energy(self):
        assert _determine_parent("dmm_energy_coal") == "dmm_energy"


class TestMineralNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(MINERAL_NODES) > 0

    def test_has_metal_category(self):
        codes = [n[0] for n in MINERAL_NODES]
        assert "dmm_metal" in codes

    def test_has_energy_category(self):
        codes = [n[0] for n in MINERAL_NODES]
        assert "dmm_energy" in codes

    def test_has_indmin_category(self):
        codes = [n[0] for n in MINERAL_NODES]
        assert "dmm_indmin" in codes

    def test_has_gold(self):
        codes = [n[0] for n in MINERAL_NODES]
        assert "dmm_metal_au" in codes

    def test_has_coal(self):
        codes = [n[0] for n in MINERAL_NODES]
        assert "dmm_energy_coal" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MINERAL_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MINERAL_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MINERAL_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MINERAL_NODES:
            if level == 2:
                assert parent is not None


def test_domain_mining_mineral_module_importable():
    assert callable(ingest_domain_mining_mineral)
    assert isinstance(MINERAL_NODES, list)


def test_ingest_domain_mining_mineral(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mining_mineral(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mining_mineral'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mining_mineral_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mining_mineral(conn)
            count2 = await ingest_domain_mining_mineral(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
