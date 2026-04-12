"""Tests for COFOG ingester.

RED tests - written before any implementation exists.

COFOG = Classification of the Functions of Government (UN Statistics Division).
Source: https://raw.githubusercontent.com/datasets/cofog/master/data/cofog.csv
License: open (UN Statistics Division)

Hierarchy:
  Division  2-digit        e.g. "01"       Level 1
  Group     X.X            e.g. "01.1"     Level 2
  Class     X.X.X          e.g. "01.1.1"   Level 3 (leaf)

10 top-level divisions (01-10), ~188 codes total.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.cofog import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    ingest_cofog,
)


class TestCofogDetermineLevel:
    def test_division_is_level_1(self):
        assert _determine_level("01") == 1

    def test_another_division_is_level_1(self):
        assert _determine_level("10") == 1

    def test_group_is_level_2(self):
        assert _determine_level("01.1") == 2

    def test_another_group_is_level_2(self):
        assert _determine_level("04.5") == 2

    def test_class_is_level_3(self):
        assert _determine_level("01.1.1") == 3

    def test_another_class_is_level_3(self):
        assert _determine_level("04.5.0") == 3


class TestCofogDetermineParent:
    def test_division_has_no_parent(self):
        assert _determine_parent("01") is None

    def test_another_division_has_no_parent(self):
        assert _determine_parent("10") is None

    def test_group_parent_is_division(self):
        assert _determine_parent("01.1") == "01"

    def test_another_group_parent_is_division(self):
        assert _determine_parent("04.5") == "04"

    def test_class_parent_is_group(self):
        assert _determine_parent("01.1.1") == "01.1"

    def test_another_class_parent_is_group(self):
        assert _determine_parent("04.5.0") == "04.5"


class TestCofogDetermineSector:
    def test_division_sector_is_itself(self):
        assert _determine_sector("01") == "01"

    def test_group_sector_is_division(self):
        assert _determine_sector("01.1") == "01"

    def test_class_sector_is_division(self):
        assert _determine_sector("01.1.1") == "01"

    def test_different_division(self):
        assert _determine_sector("07.2.0") == "07"

    def test_division_10(self):
        assert _determine_sector("10") == "10"

    def test_group_10(self):
        assert _determine_sector("10.1") == "10"


def test_cofog_module_importable():
    assert callable(ingest_cofog)
    assert callable(_determine_level)
    assert callable(_determine_parent)
    assert callable(_determine_sector)


def test_ingest_cofog(db_pool):
    """Integration test: ingest COFOG from GitHub CSV."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_cofog(conn)
            assert count >= 180, f"Expected >= 180 COFOG codes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'cofog'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Verify hierarchy
            div = await conn.fetchrow(
                "SELECT level, parent_code, sector_code FROM classification_node "
                "WHERE system_id = 'cofog' AND code = '01'"
            )
            assert div["level"] == 1
            assert div["parent_code"] is None
            assert div["sector_code"] == "01"

            grp = await conn.fetchrow(
                "SELECT level, parent_code, sector_code FROM classification_node "
                "WHERE system_id = 'cofog' AND code = '01.1'"
            )
            assert grp["level"] == 2
            assert grp["parent_code"] == "01"
            assert grp["sector_code"] == "01"

            cls = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'cofog' AND code = '01.1.1'"
            )
            assert cls["level"] == 3
            assert cls["parent_code"] == "01.1"
            assert cls["is_leaf"] is True

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_cofog_idempotent(db_pool):
    """Running ingest twice returns the same count."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_cofog(conn)
            count2 = await ingest_cofog(conn)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
