"""Tests for ISCO-08 (International Standard Classification of Occupations) ingester.

RED tests - written before any implementation exists.

Hierarchy (level determined by code length):
  L1 - Major Group     (1-digit, e.g. "1"    = Managers)
  L2 - Sub-major Group (2-digit, e.g. "11"   = Chief Executives, Senior Officials...)
  L3 - Minor Group     (3-digit, e.g. "111"  = Legislators and Senior Officials)
  L4 - Unit Group      (4-digit, e.g. "1111" = Legislators) - leaf

Source: ILO (International Labour Organization), public access
  https://webapps.ilo.org/ilostat-files/ISCO/newdocs-08-2021/ISCO-08/ISCO-08%20EN.csv
"""
import asyncio
import pytest
from pathlib import Path

from world_of_taxanomy.ingest.isco_08 import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    ingest_isco_08,
)


class TestIsco08DetermineLevel:
    def test_1digit_is_major_level_1(self):
        assert _determine_level("1") == 1

    def test_0_armed_forces_is_level_1(self):
        assert _determine_level("0") == 1

    def test_9_elementary_is_level_1(self):
        assert _determine_level("9") == 1

    def test_2digit_is_submajor_level_2(self):
        assert _determine_level("11") == 2

    def test_another_2digit_is_level_2(self):
        assert _determine_level("53") == 2

    def test_3digit_is_minor_level_3(self):
        assert _determine_level("111") == 3

    def test_another_3digit_is_level_3(self):
        assert _determine_level("532") == 3

    def test_4digit_is_unit_level_4(self):
        assert _determine_level("1111") == 4

    def test_another_4digit_is_level_4(self):
        assert _determine_level("9333") == 4


class TestIsco08DetermineParent:
    def test_major_has_no_parent(self):
        assert _determine_parent("1") is None

    def test_zero_major_has_no_parent(self):
        assert _determine_parent("0") is None

    def test_submajor_parent_is_major(self):
        assert _determine_parent("11") == "1"

    def test_another_submajor_parent_is_major(self):
        assert _determine_parent("91") == "9"

    def test_minor_parent_is_submajor(self):
        assert _determine_parent("111") == "11"

    def test_another_minor_parent_is_submajor(self):
        assert _determine_parent("532") == "53"

    def test_unit_parent_is_minor(self):
        assert _determine_parent("1111") == "111"

    def test_another_unit_parent_is_minor(self):
        assert _determine_parent("9333") == "933"


class TestIsco08DetermineSector:
    def test_major_sector_is_itself(self):
        assert _determine_sector("1") == "1"

    def test_submajor_sector_is_major(self):
        assert _determine_sector("11") == "1"

    def test_minor_sector_is_major(self):
        assert _determine_sector("111") == "1"

    def test_unit_sector_is_major(self):
        assert _determine_sector("1111") == "1"

    def test_zero_family(self):
        assert _determine_sector("0110") == "0"


def test_isco_08_module_importable():
    """All public symbols are importable."""
    assert callable(ingest_isco_08)
    assert callable(_determine_level)
    assert callable(_determine_parent)
    assert callable(_determine_sector)


def test_ingest_isco_08_from_file(db_pool):
    """Integration test - ingest from downloaded CSV."""
    data_path = Path("data/isco_08.csv")
    if not data_path.exists():
        pytest.skip(
            "Download data/isco_08.csv first: "
            "https://webapps.ilo.org/ilostat-files/ISCO/newdocs-08-2021/"
            "ISCO-08/ISCO-08%20EN.csv"
        )

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_isco_08(conn, path=str(data_path))
            # 10 major + 43 sub-major + 130 minor + 436 unit = 619
            assert count >= 600, f"Expected >= 600 nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'isco_08'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Major Group "1" at level 1, no parent, not leaf
            major = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'isco_08' AND code = '1'"
            )
            assert major is not None
            assert major["level"] == 1
            assert major["parent_code"] is None
            assert major["is_leaf"] is False

            # Sub-major "11" at level 2, parent "1"
            sub = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'isco_08' AND code = '11'"
            )
            assert sub is not None
            assert sub["level"] == 2
            assert sub["parent_code"] == "1"

            # Minor "111" at level 3, parent "11"
            minor = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'isco_08' AND code = '111'"
            )
            assert minor is not None
            assert minor["level"] == 3
            assert minor["parent_code"] == "11"

            # Unit "1111" (Legislators) at level 4, parent "111", is_leaf
            unit = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'isco_08' AND code = '1111'"
            )
            assert unit is not None
            assert unit["level"] == 4
            assert unit["parent_code"] == "111"
            assert unit["is_leaf"] is True

            # Armed Forces "0" at level 1, no parent
            armed = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'isco_08' AND code = '0'"
            )
            assert armed is not None
            assert armed["level"] == 1
            assert armed["parent_code"] is None

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_isco_08_idempotent(db_pool):
    """Running ingest twice does not raise and returns consistent count."""
    data_path = Path("data/isco_08.csv")
    if not data_path.exists():
        pytest.skip("Download data/isco_08.csv first")

    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_isco_08(conn, path=str(data_path))
            count2 = await ingest_isco_08(conn, path=str(data_path))
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
