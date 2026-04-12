"""Tests for Truck Vehicle Class domain taxonomy ingester.

RED tests - written before any implementation exists.

Vehicle Class Taxonomy covers:
  DOT Classes (dtv_dot*)  - GVWR-based DOT weight classes 1-8
  Body Types  (dtv_body*) - specific vehicle body configurations

DOT Class definitions (GVWR ranges):
  Class 1: < 6,000 lbs    (light duty - pickup trucks)
  Class 2: 6,001-10,000   (light duty - larger pickups)
  Class 3: 10,001-14,000  (medium duty - cargo vans, small box trucks)
  Class 4: 14,001-16,000  (medium duty - city delivery)
  Class 5: 16,001-19,500  (medium duty - large walk-in)
  Class 6: 19,501-26,000  (medium duty - single axle straight)
  Class 7: 26,001-33,000  (heavy duty - city transit, tractor)
  Class 8: > 33,000 lbs   (heavy duty - semi trucks, heavy straight)

Source: DOT Federal Motor Carrier Safety Administration. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_truck_vehicle import (
    VEHICLE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_truck_vehicle,
)


class TestDetermineLevel:
    def test_dot_category_is_level_1(self):
        assert _determine_level("dtv_dot") == 1

    def test_dot_class_is_level_2(self):
        assert _determine_level("dtv_dot_8") == 2

    def test_body_category_is_level_1(self):
        assert _determine_level("dtv_body") == 1

    def test_body_type_is_level_2(self):
        assert _determine_level("dtv_body_semi") == 2


class TestDetermineParent:
    def test_dot_category_has_no_parent(self):
        assert _determine_parent("dtv_dot") is None

    def test_dot_class_8_parent_is_dot(self):
        assert _determine_parent("dtv_dot_8") == "dtv_dot"

    def test_body_semi_parent_is_body(self):
        assert _determine_parent("dtv_body_semi") == "dtv_body"


class TestVehicleNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(VEHICLE_NODES) > 0

    def test_has_dot_category(self):
        codes = [n[0] for n in VEHICLE_NODES]
        assert "dtv_dot" in codes

    def test_has_body_category(self):
        codes = [n[0] for n in VEHICLE_NODES]
        assert "dtv_body" in codes

    def test_has_class_8(self):
        codes = [n[0] for n in VEHICLE_NODES]
        assert "dtv_dot_8" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in VEHICLE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in VEHICLE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in VEHICLE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in VEHICLE_NODES:
            if level == 2:
                assert parent is not None


def test_domain_truck_vehicle_module_importable():
    assert callable(ingest_domain_truck_vehicle)
    assert isinstance(VEHICLE_NODES, list)


def test_ingest_domain_truck_vehicle(db_pool):
    """Integration test: vehicle taxonomy rows + NAICS links."""
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_truck_vehicle(conn)
            assert count > 0

            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_truck_vehicle'"
            )
            assert row is not None
            assert row["code_count"] == count

            link_count = await conn.fetchval(
                "SELECT COUNT(*) FROM node_taxonomy_link "
                "WHERE taxonomy_id = 'domain_truck_vehicle'"
            )
            assert link_count > 0

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_truck_vehicle_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_truck_vehicle(conn)
            count2 = await ingest_domain_truck_vehicle(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
