"""Tests for SOC 2018 (Standard Occupational Classification) ingester.

RED tests - written before any implementation exists.

Hierarchy (codes are "XX-XXXX" format, level by trailing zeros):
  L1 - Major Group       (ends in "0000",  e.g. "11-0000" Management Occupations)
  L2 - Minor Group       (ends in "000",   e.g. "11-1000" Top Executives)
  L3 - Broad Occupation  (ends in "0",     e.g. "11-1010" Chief Executives)
  L4 - Detailed Occupation (no trailing 0, e.g. "11-1011") - leaf

O*NET extensions (codes with decimal, e.g. "11-1011.03") are skipped.

Source: US Bureau of Labor Statistics, SOC 2018
  Mirror: Budget Lab at Yale (public, no auth)
  https://github.com/Budget-Lab-Yale/AI-Employment-Model/blob/main/resources/SOC_Structure.csv
"""
import asyncio
import pytest
from pathlib import Path

from world_of_taxanomy.ingest.soc_2018 import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    ingest_soc_2018,
)


class TestSoc2018DetermineLevel:
    def test_major_group_is_level_1(self):
        assert _determine_level("11-0000") == 1

    def test_another_major_group_is_level_1(self):
        assert _determine_level("53-0000") == 1

    def test_minor_group_is_level_2(self):
        assert _determine_level("11-1000") == 2

    def test_another_minor_group_is_level_2(self):
        assert _determine_level("11-9000") == 2

    def test_broad_occupation_is_level_3(self):
        assert _determine_level("11-1010") == 3

    def test_another_broad_occupation_is_level_3(self):
        assert _determine_level("11-2020") == 3

    def test_detailed_occupation_is_level_4(self):
        assert _determine_level("11-1011") == 4

    def test_another_detailed_occupation_is_level_4(self):
        assert _determine_level("11-2021") == 4


class TestSoc2018DetermineParent:
    def test_major_group_has_no_parent(self):
        assert _determine_parent("11-0000") is None

    def test_another_major_group_has_no_parent(self):
        assert _determine_parent("53-0000") is None

    def test_minor_group_parent_is_major(self):
        assert _determine_parent("11-1000") == "11-0000"

    def test_another_minor_group_parent_is_major(self):
        assert _determine_parent("11-9000") == "11-0000"

    def test_broad_parent_is_minor(self):
        assert _determine_parent("11-1010") == "11-1000"

    def test_broad_parent_is_minor_2(self):
        assert _determine_parent("11-2020") == "11-2000"

    def test_detailed_parent_is_broad(self):
        assert _determine_parent("11-1011") == "11-1010"

    def test_detailed_parent_is_broad_2(self):
        assert _determine_parent("11-2021") == "11-2020"


class TestSoc2018DetermineSector:
    def test_major_group_sector_is_itself(self):
        assert _determine_sector("11-0000") == "11-0000"

    def test_minor_group_sector_is_major(self):
        assert _determine_sector("11-1000") == "11-0000"

    def test_broad_sector_is_major(self):
        assert _determine_sector("11-1010") == "11-0000"

    def test_detailed_sector_is_major(self):
        assert _determine_sector("11-1011") == "11-0000"

    def test_different_major_family(self):
        assert _determine_sector("53-7051") == "53-0000"


def test_soc_2018_module_importable():
    """All public symbols are importable."""
    assert callable(ingest_soc_2018)
    assert callable(_determine_level)
    assert callable(_determine_parent)
    assert callable(_determine_sector)


def test_ingest_soc_2018_from_file(db_pool):
    """Integration test - ingest from downloaded CSV."""
    data_path = Path("data/soc_2018.csv")
    if not data_path.exists():
        pytest.skip(
            "Download data/soc_2018.csv first: "
            "https://raw.githubusercontent.com/Budget-Lab-Yale/AI-Employment-Model"
            "/main/resources/SOC_Structure.csv"
        )

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_soc_2018(conn, path=str(data_path))
            # 23 majors + 98 minors + 459 broads + 867 details = 1,447
            assert count >= 1400, f"Expected >= 1400 nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'soc_2018'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Major Group "11-0000" at level 1, no parent, not leaf
            major = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'soc_2018' AND code = '11-0000'"
            )
            assert major is not None
            assert major["level"] == 1
            assert major["parent_code"] is None
            assert major["is_leaf"] is False

            # Minor Group "11-1000" at level 2, parent "11-0000"
            minor = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'soc_2018' AND code = '11-1000'"
            )
            assert minor is not None
            assert minor["level"] == 2
            assert minor["parent_code"] == "11-0000"

            # Broad Occupation "11-1010" at level 3, parent "11-1000"
            broad = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'soc_2018' AND code = '11-1010'"
            )
            assert broad is not None
            assert broad["level"] == 3
            assert broad["parent_code"] == "11-1000"

            # Detailed Occupation "11-1011" at level 4, parent "11-1010", is_leaf
            detail = await conn.fetchrow(
                "SELECT code, level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'soc_2018' AND code = '11-1011'"
            )
            assert detail is not None
            assert detail["level"] == 4
            assert detail["parent_code"] == "11-1010"
            assert detail["is_leaf"] is True

            # O*NET extension "11-1011.03" must NOT be in the DB
            onet = await conn.fetchrow(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'soc_2018' AND code = '11-1011.03'"
            )
            assert onet is None, "O*NET extension codes must not be ingested"

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_soc_2018_idempotent(db_pool):
    """Running ingest twice does not raise and returns consistent count."""
    data_path = Path("data/soc_2018.csv")
    if not data_path.exists():
        pytest.skip("Download data/soc_2018.csv first")

    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_soc_2018(conn, path=str(data_path))
            count2 = await ingest_soc_2018(conn, path=str(data_path))
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
