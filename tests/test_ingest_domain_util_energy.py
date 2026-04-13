"""Tests for Utility Energy Source domain taxonomy ingester.

RED tests - written before any implementation exists.

Energy source taxonomy organizes electricity generation methods:
  Fossil Fuels (due_fossil*) - coal, natural gas, oil
  Nuclear      (due_nuclear*) - fission, SMR
  Renewable    (due_renew*)  - solar, wind, hydro, geothermal, biomass
  Storage      (due_storage*) - battery, pumped hydro, hydrogen

Source: IEA energy source classifications + EIA. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_util_energy import (
    ENERGY_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_util_energy,
)


class TestDetermineLevel:
    def test_fossil_category_is_level_1(self):
        assert _determine_level("due_fossil") == 1

    def test_coal_is_level_2(self):
        assert _determine_level("due_fossil_coal") == 2

    def test_renew_category_is_level_1(self):
        assert _determine_level("due_renew") == 1

    def test_solar_is_level_2(self):
        assert _determine_level("due_renew_solar") == 2


class TestDetermineParent:
    def test_fossil_category_has_no_parent(self):
        assert _determine_parent("due_fossil") is None

    def test_coal_parent_is_fossil(self):
        assert _determine_parent("due_fossil_coal") == "due_fossil"

    def test_solar_parent_is_renew(self):
        assert _determine_parent("due_renew_solar") == "due_renew"


class TestEnergyNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(ENERGY_NODES) > 0

    def test_has_fossil_category(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert "due_fossil" in codes

    def test_has_nuclear_category(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert "due_nuclear" in codes

    def test_has_renewable_category(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert "due_renew" in codes

    def test_has_coal(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert "due_fossil_coal" in codes

    def test_has_solar(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert "due_renew_solar" in codes

    def test_has_wind(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert "due_renew_wind" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in ENERGY_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in ENERGY_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in ENERGY_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in ENERGY_NODES:
            if level == 2:
                assert parent is not None


def test_domain_util_energy_module_importable():
    assert callable(ingest_domain_util_energy)
    assert isinstance(ENERGY_NODES, list)


def test_ingest_domain_util_energy(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_util_energy(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_util_energy'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_util_energy_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_util_energy(conn)
            count2 = await ingest_domain_util_energy(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
