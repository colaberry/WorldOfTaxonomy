"""Tests for Truck Geographic Lane Classification domain taxonomy ingester.

RED tests - written before any implementation exists.

Trucking Lane taxonomy classifies geographic lane types - orthogonal to
freight mode, vehicle class, cargo type, carrier ops, pricing, and regulatory:
  Haul Distance     (dtl_dist*)     - local, short, regional, long-haul, OTR
  Geographic Corridor (dtl_geo*)    - Northeast, Southeast, Midwest, Southwest, etc.
  Cross-Border/Intl (dtl_border*)   - US-Canada, US-Mexico, international
  Last Mile         (dtl_lastmile*) - urban, suburban, rural, residential, on-demand
  Lane Density      (dtl_density*)  - high, medium, low-density, backhaul

Stakeholders: network planners, rate analysts, load matchers, capacity managers,
logistics real estate developers.
Source: DAT lane analytics, FMCSA freight analysis framework, ATRI corridor data.
Hand-coded.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_lane import (
    LANE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_lane,
)


class TestDetermineLevel:
    def test_dist_category_is_level_1(self):
        assert _determine_level("dtl_dist") == 1

    def test_local_is_level_2(self):
        assert _determine_level("dtl_dist_local") == 2

    def test_geo_category_is_level_1(self):
        assert _determine_level("dtl_geo") == 1

    def test_northeast_is_level_2(self):
        assert _determine_level("dtl_geo_ne") == 2

    def test_border_category_is_level_1(self):
        assert _determine_level("dtl_border") == 1

    def test_lastmile_category_is_level_1(self):
        assert _determine_level("dtl_lastmile") == 1

    def test_density_category_is_level_1(self):
        assert _determine_level("dtl_density") == 1


class TestDetermineParent:
    def test_dist_category_has_no_parent(self):
        assert _determine_parent("dtl_dist") is None

    def test_local_parent_is_dist(self):
        assert _determine_parent("dtl_dist_local") == "dtl_dist"

    def test_geo_ne_parent_is_geo(self):
        assert _determine_parent("dtl_geo_ne") == "dtl_geo"

    def test_border_us_ca_parent_is_border(self):
        assert _determine_parent("dtl_border_us_ca") == "dtl_border"

    def test_lastmile_urban_parent_is_lastmile(self):
        assert _determine_parent("dtl_lastmile_urban") == "dtl_lastmile"


class TestLaneNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(LANE_NODES) > 0

    def test_has_distance_category(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_dist" in codes

    def test_has_corridor_category(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_geo" in codes

    def test_has_border_category(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_border" in codes

    def test_has_lastmile_category(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_lastmile" in codes

    def test_has_density_category(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_density" in codes

    def test_has_long_haul_node(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_dist_longhaul" in codes

    def test_has_us_mexico_border(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_border_us_mx" in codes

    def test_has_urban_lastmile(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_lastmile_urban" in codes

    def test_has_backhaul_density(self):
        codes = [n[0] for n in LANE_NODES]
        assert "dtl_density_backhaul" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in LANE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in LANE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in LANE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in LANE_NODES:
            if level == 2:
                assert parent is not None

    def test_minimum_node_count(self):
        assert len(LANE_NODES) >= 20

    def test_no_em_dashes_in_titles(self):
        for code, title, level, parent in LANE_NODES:
            assert "\u2014" not in title, f"Em-dash in title for '{code}'"


def test_domain_truck_lane_module_importable():
    assert callable(ingest_domain_truck_lane)
    assert isinstance(LANE_NODES, list)


def test_ingest_domain_truck_lane(db_pool):
    """Integration test: lane taxonomy rows + NAICS 484 links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_lane(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_lane'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_lane'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_lane_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_lane(conn)
            count2 = await ingest_domain_truck_lane(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
