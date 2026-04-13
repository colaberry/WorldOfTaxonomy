"""Tests for Transportation Mode domain taxonomy ingester.

RED tests - written before any implementation exists.

Transportation mode taxonomy organizes non-truck transport (NAICS 48-49):
  Air Transport    (dtm_air*)   - commercial airline, cargo, charter, general aviation
  Rail Transport   (dtm_rail*)  - freight rail, passenger rail, commuter rail
  Water Transport  (dtm_water*) - deep sea, coastal, inland waterway, ferry
  Pipeline         (dtm_pipe*)  - crude oil, natural gas, products, water
  Other            (dtm_other*) - courier/express, postal service, scenic/sightseeing

Source: DOT (US Department of Transportation) modal categories. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_transport_mode import (
    TRANSPORT_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_transport_mode,
)


class TestDetermineLevel:
    def test_air_category_is_level_1(self):
        assert _determine_level("dtm_air") == 1

    def test_airline_is_level_2(self):
        assert _determine_level("dtm_air_airline") == 2

    def test_rail_category_is_level_1(self):
        assert _determine_level("dtm_rail") == 1

    def test_freight_rail_is_level_2(self):
        assert _determine_level("dtm_rail_freight") == 2


class TestDetermineParent:
    def test_air_category_has_no_parent(self):
        assert _determine_parent("dtm_air") is None

    def test_airline_parent_is_air(self):
        assert _determine_parent("dtm_air_airline") == "dtm_air"

    def test_freight_rail_parent_is_rail(self):
        assert _determine_parent("dtm_rail_freight") == "dtm_rail"


class TestTransportNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(TRANSPORT_NODES) > 0

    def test_has_air_category(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert "dtm_air" in codes

    def test_has_rail_category(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert "dtm_rail" in codes

    def test_has_water_category(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert "dtm_water" in codes

    def test_has_pipeline_category(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert "dtm_pipe" in codes

    def test_has_airline(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert "dtm_air_airline" in codes

    def test_has_freight_rail(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert "dtm_rail_freight" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in TRANSPORT_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in TRANSPORT_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in TRANSPORT_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in TRANSPORT_NODES:
            if level == 2:
                assert parent is not None


def test_domain_transport_mode_module_importable():
    assert callable(ingest_domain_transport_mode)
    assert isinstance(TRANSPORT_NODES, list)


def test_ingest_domain_transport_mode(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_transport_mode(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_transport_mode'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_transport_mode_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_transport_mode(conn)
            count2 = await ingest_domain_transport_mode(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
