"""Tests for ICD-11 MMS ingester.

RED tests - written before any implementation exists.

ICD-11 Mortality and Morbidity Statistics (MMS) linearization.
Source: WHO ICD-11 API (free registration required)
  https://icd.who.int/icdapi
  Download: register -> get token -> download linearization CSV
  Or: use the WHO ICD-11 browser Export to Excel (icd.who.int/browse/2024-01/mms)

Expected CSV format (WHO linearization export):
  Columns: Code, Title, ParentCode (parent is empty for root/chapter nodes)
  ~35,000-55,000 MMS codes depending on version.

Hierarchy: ICD-11 uses alphanumeric codes. Hierarchy is NOT derivable from the
code alone - it is encoded in the ParentCode column of the linearization file.
The ingester reads ParentCode directly from the CSV.

License: CC BY-ND 3.0 IGO (attribution required, no derivatives)
"""
import asyncio
import pytest
from pathlib import Path

from world_of_taxanomy.ingest.icd_11 import (
    _parse_level,
    _parse_sector,
    ingest_icd_11,
)


class TestIcd11ParseLevel:
    """Level is derived from position in the hierarchy (depth from root).

    In practice: computed from parent chain depth.
    The ingester builds levels after reading all parent/child relationships.
    For unit-testing, _parse_level takes a pre-computed depth integer.
    """

    def test_depth_0_is_level_1(self):
        assert _parse_level(0) == 1

    def test_depth_1_is_level_2(self):
        assert _parse_level(1) == 2

    def test_depth_5_is_level_6(self):
        assert _parse_level(5) == 6


class TestIcd11ParseSector:
    """Sector is the chapter code - the root ancestor of any node."""

    def test_code_with_no_parent_is_own_sector(self):
        # A chapter node is its own sector
        assert _parse_sector("1A00", {}) == "1A00"

    def test_code_with_parent_chains_to_root(self):
        # Build a parent map: 1A00 -> None (chapter), 1A01 -> 1A00
        parent_map = {"1A01": "1A00"}
        assert _parse_sector("1A01", parent_map) == "1A00"

    def test_code_chains_two_levels(self):
        parent_map = {"1A00.0": "1A00", "1A00": "1A"}
        assert _parse_sector("1A00.0", parent_map) == "1A"

    def test_nested_chain(self):
        parent_map = {"leaf": "mid", "mid": "top"}
        assert _parse_sector("leaf", parent_map) == "top"


def test_icd_11_module_importable():
    """All public symbols are importable."""
    assert callable(ingest_icd_11)
    assert callable(_parse_level)
    assert callable(_parse_sector)


def test_ingest_icd_11_from_file(db_pool):
    """Integration test - ingest from WHO linearization CSV.

    To obtain the file:
      1. Register at https://icd.who.int/icdapi (free)
      2. Download the ICD-11 MMS linearization spreadsheet
         (Browse -> Export/Download, select 'Linearization')
      3. Save as data/icd_11.csv with columns: Code, Title, ParentCode
         (ParentCode is empty for chapter-level nodes)
    """
    data_path = Path("data/icd_11.csv")
    if not data_path.exists():
        pytest.skip(
            "Download data/icd_11.csv from https://icd.who.int/icdapi "
            "(free registration required). Export the MMS linearization "
            "with columns: Code, Title, ParentCode"
        )

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_icd_11(conn, path=str(data_path))
            # MMS has 35,000+ codes depending on version
            assert count >= 10000, f"Expected >= 10000 nodes, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system WHERE id = 'icd_11'"
            )
            assert row is not None
            assert row["node_count"] == count

            # At least one chapter-level node with no parent
            root = await conn.fetchrow(
                "SELECT code, level, parent_code FROM classification_node "
                "WHERE system_id = 'icd_11' AND parent_code IS NULL LIMIT 1"
            )
            assert root is not None
            assert root["level"] == 1

            # Leaf nodes should exist
            leaf = await conn.fetchrow(
                "SELECT code, is_leaf FROM classification_node "
                "WHERE system_id = 'icd_11' AND is_leaf IS TRUE LIMIT 1"
            )
            assert leaf is not None

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_icd_11_idempotent(db_pool):
    """Running ingest twice returns consistent count."""
    data_path = Path("data/icd_11.csv")
    if not data_path.exists():
        pytest.skip("Download data/icd_11.csv from https://icd.who.int/icdapi first")

    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_icd_11(conn, path=str(data_path))
            count2 = await ingest_icd_11(conn, path=str(data_path))
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
