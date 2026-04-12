"""Tests for UN M.49 Regions ingester.

RED tests - written before any implementation exists.

Hierarchy:
  L0 - World (code "001")
  L1 - Region (e.g. "002" Africa, "019" Americas, "142" Asia)
  L2 - Sub-region (e.g. "014" Eastern Africa, "021" Northern America)
  L3 - Country (numeric M.49 code, e.g. "840" = United States)

Source: unstats.un.org/unsd/methodology/m49/overview (CSV download)
License: open (UN Statistics Division)
"""
import pytest
from world_of_taxanomy.ingest.un_m49 import (
    _WORLD_CODE,
    _determine_level,
    _determine_parent,
    ingest_un_m49,
)


class TestUnM49DetermineLevel:
    def test_world_is_level_0(self):
        assert _determine_level("001") == 0

    def test_region_africa_is_level_1(self):
        assert _determine_level("002") == 1

    def test_region_americas_is_level_1(self):
        assert _determine_level("019") == 1

    def test_subregion_eastern_africa_is_level_2(self):
        assert _determine_level("014") == 2

    def test_country_is_level_3(self):
        # Country-level M.49 codes are determined by context (not code pattern alone)
        # The ingester passes the level directly from the CSV
        # These tests verify the helper handles the levels correctly
        assert _determine_level("840") == 3  # United States

    def test_world_code_constant_is_001(self):
        assert _WORLD_CODE == "001"


class TestUnM49DetermineParent:
    def test_world_has_no_parent(self):
        assert _determine_parent("001", level=0) is None

    def test_region_parent_is_world(self):
        assert _determine_parent("002", level=1) == "001"

    def test_subregion_parent_provided_explicitly(self):
        # Sub-region parent is the region code passed in from CSV
        assert _determine_parent("014", level=2, region_code="002") == "002"

    def test_country_parent_provided_explicitly(self):
        # Country parent is the sub-region code passed in from CSV
        assert _determine_parent("840", level=3, subregion_code="021") == "021"

    def test_subregion_without_region_falls_back_to_world(self):
        assert _determine_parent("014", level=2, region_code=None) == "001"


def test_ingest_un_m49_from_csv(db_pool):
    """Integration test - ingest from downloaded CSV."""
    import asyncio
    from pathlib import Path

    data_path = Path("data/un_m49.csv")
    if not data_path.exists():
        pytest.skip(f"Download {data_path} first: see world_of_taxanomy/ingest/un_m49.py for URL")

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_un_m49(conn, path=str(data_path))
            assert count >= 200, f"Expected >= 200 nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'un_m49'"
            )
            assert row is not None
            assert row["node_count"] == count

            # World node must exist at level 0
            world = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'un_m49' AND code = '001'"
            )
            assert world is not None
            assert world["level"] == 0
            assert world["parent_code"] is None

            # Africa region at level 1, parent is World
            africa = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'un_m49' AND code = '002'"
            )
            assert africa is not None
            assert africa["level"] == 1
            assert africa["parent_code"] == "001"

            # US country node at level 3 (M.49 code 840)
            us = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'un_m49' AND code = '840'"
            )
            assert us is not None
            assert us["level"] == 3

    asyncio.get_event_loop().run_until_complete(_run())
