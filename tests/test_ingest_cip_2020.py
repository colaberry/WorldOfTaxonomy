"""Tests for CIP 2020 (Classification of Instructional Programs) ingester.

RED tests - written before any implementation exists.

Hierarchy (level determined by code format):
  L1 - Family  (2-digit, no period,   e.g. "01" = Agricultural/Animal/Plant...)
  L2 - Area    (XX.XX format,         e.g. "01.01" = Agricultural Business...)
  L3 - Program (XX.XXXX format, leaf, e.g. "01.0101" = Agricultural Business, General)

Codes in CSV use Excel-escape prefix ='XX' which must be stripped.

Source: NCES (National Center for Education Statistics), public domain
  https://nces.ed.gov/ipeds/cipcode/Files/CIPCode2020.csv
"""
import asyncio
import pytest
from pathlib import Path

from world_of_taxanomy.ingest.cip_2020 import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    _clean_code,
    ingest_cip_2020,
)


class TestCip2020CleanCode:
    def test_strips_excel_prefix(self):
        assert _clean_code('="01"') == "01"

    def test_strips_excel_prefix_program(self):
        assert _clean_code('="01.0000"') == "01.0000"

    def test_plain_code_unchanged(self):
        assert _clean_code("01") == "01"

    def test_strips_equals_quote(self):
        assert _clean_code('="44.0201"') == "44.0201"


class TestCip2020DetermineLevel:
    def test_family_is_level_1(self):
        assert _determine_level("01") == 1

    def test_another_family_is_level_1(self):
        assert _determine_level("52") == 1

    def test_area_is_level_2(self):
        assert _determine_level("01.00") == 2

    def test_another_area_is_level_2(self):
        assert _determine_level("01.01") == 2

    def test_program_is_level_3(self):
        assert _determine_level("01.0000") == 3

    def test_another_program_is_level_3(self):
        assert _determine_level("01.0101") == 3

    def test_high_numbered_family_is_level_1(self):
        assert _determine_level("54") == 1


class TestCip2020DetermineParent:
    def test_family_has_no_parent(self):
        assert _determine_parent("01") is None

    def test_area_parent_is_family(self):
        assert _determine_parent("01.00") == "01"

    def test_another_area_parent_is_family(self):
        assert _determine_parent("01.01") == "01"

    def test_program_parent_is_area(self):
        assert _determine_parent("01.0000") == "01.00"

    def test_another_program_parent_is_area(self):
        assert _determine_parent("01.0101") == "01.01"

    def test_program_52_parent(self):
        assert _determine_parent("52.0201") == "52.02"


class TestCip2020DetermineSector:
    def test_family_sector_is_itself(self):
        assert _determine_sector("01") == "01"

    def test_area_sector_is_family(self):
        assert _determine_sector("01.01") == "01"

    def test_program_sector_is_family(self):
        assert _determine_sector("01.0101") == "01"

    def test_high_family_sector(self):
        assert _determine_sector("52.0201") == "52"


def test_cip_2020_module_importable():
    """All public symbols are importable."""
    assert callable(ingest_cip_2020)
    assert callable(_determine_level)
    assert callable(_determine_parent)
    assert callable(_determine_sector)
    assert callable(_clean_code)


def test_ingest_cip_2020_from_file(db_pool):
    """Integration test - ingest from downloaded CSV."""
    data_path = Path("data/cip_2020.csv")
    if not data_path.exists():
        pytest.skip(
            "Download data/cip_2020.csv first: "
            "https://nces.ed.gov/ipeds/cipcode/Files/CIPCode2020.csv"
        )

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_cip_2020(conn, path=str(data_path))
            # 50 families + 473 areas + 2325 programs = 2848
            assert count >= 2800, f"Expected >= 2800 nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'cip_2020'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Family "01" at level 1, no parent, not leaf
            fam = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'cip_2020' AND code = '01'"
            )
            assert fam is not None
            assert fam["level"] == 1
            assert fam["parent_code"] is None
            assert fam["is_leaf"] is False

            # Area "01.01" at level 2, parent "01"
            area = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'cip_2020' AND code = '01.01'"
            )
            assert area is not None
            assert area["level"] == 2
            assert area["parent_code"] == "01"

            # Program "01.0101" at level 3, parent "01.01", is_leaf
            prog = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'cip_2020' AND code = '01.0101'"
            )
            assert prog is not None
            assert prog["level"] == 3
            assert prog["parent_code"] == "01.01"
            assert prog["is_leaf"] is True

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_cip_2020_idempotent(db_pool):
    """Running ingest twice does not raise and returns consistent count."""
    data_path = Path("data/cip_2020.csv")
    if not data_path.exists():
        pytest.skip("Download data/cip_2020.csv first")

    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_cip_2020(conn, path=str(data_path))
            count2 = await ingest_cip_2020(conn, path=str(data_path))
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
