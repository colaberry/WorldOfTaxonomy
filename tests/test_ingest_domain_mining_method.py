"""Tests for Mining Extraction Method domain taxonomy ingester.

RED tests - written before any implementation exists.

Extraction method taxonomy organizes mining techniques into categories:
  Surface Mining   (dme_surface*)   - open-pit, strip, dredge, quarry
  Underground      (dme_underground*) - room-and-pillar, longwall, shaft
  Fluid Extraction (dme_fluid*)     - drilling, fracking, solution mining
  Processing       (dme_process*)   - crushing, flotation, smelting, leaching

Source: SME (Society for Mining, Metallurgy and Exploration). Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_mining_method import (
    MINING_METHOD_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_mining_method,
)


class TestDetermineLevel:
    def test_surface_category_is_level_1(self):
        assert _determine_level("dme_surface") == 1

    def test_surface_type_is_level_2(self):
        assert _determine_level("dme_surface_open") == 2

    def test_underground_category_is_level_1(self):
        assert _determine_level("dme_underground") == 1

    def test_underground_type_is_level_2(self):
        assert _determine_level("dme_underground_long") == 2


class TestDetermineParent:
    def test_surface_category_has_no_parent(self):
        assert _determine_parent("dme_surface") is None

    def test_open_pit_parent_is_surface(self):
        assert _determine_parent("dme_surface_open") == "dme_surface"

    def test_longwall_parent_is_underground(self):
        assert _determine_parent("dme_underground_long") == "dme_underground"


class TestMiningMethodNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(MINING_METHOD_NODES) > 0

    def test_has_surface_category(self):
        codes = [n[0] for n in MINING_METHOD_NODES]
        assert "dme_surface" in codes

    def test_has_underground_category(self):
        codes = [n[0] for n in MINING_METHOD_NODES]
        assert "dme_underground" in codes

    def test_has_fluid_category(self):
        codes = [n[0] for n in MINING_METHOD_NODES]
        assert "dme_fluid" in codes

    def test_has_open_pit(self):
        codes = [n[0] for n in MINING_METHOD_NODES]
        assert "dme_surface_open" in codes

    def test_has_fracking(self):
        codes = [n[0] for n in MINING_METHOD_NODES]
        assert "dme_fluid_frack" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in MINING_METHOD_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in MINING_METHOD_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in MINING_METHOD_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in MINING_METHOD_NODES:
            if level == 2:
                assert parent is not None


def test_domain_mining_method_module_importable():
    assert callable(ingest_domain_mining_method)
    assert isinstance(MINING_METHOD_NODES, list)


def test_ingest_domain_mining_method(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_mining_method(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_mining_method'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_mining_method_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_mining_method(conn)
            count2 = await ingest_domain_mining_method(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
