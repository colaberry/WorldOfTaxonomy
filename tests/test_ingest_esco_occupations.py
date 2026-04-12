"""Tests for ESCO Occupations ingester.

RED tests - written before any implementation exists.

ESCO = European Skills, Competences, Qualifications and Occupations framework.
Published by the European Commission, available as bulk CSV download.
License: CC BY 4.0

ESCO Occupations are level-5 specialisations beneath ISCO-08 unit groups.
Stored as a flat system (all level=1, no parent) in WorldOfTaxanomy.
The link to ISCO-08 is handled by the crosswalk in Phase 7-C.

Structure:
  ~2,942 occupation nodes (v1.1.1) / ~3,000 nodes (v1.2.0+)
  code = UUID extracted from conceptUri
  title = preferredLabel (English)
  level = 1 (all flat)
  parent_code = None
  sector_code = first digit of ISCO-08 group code
  is_leaf = True (all leaves)

Source: https://esco.ec.europa.eu/en/use-esco/download
"""
import asyncio
import os
import pytest

from world_of_taxanomy.ingest.esco_occupations import (
    _extract_code,
    _determine_sector,
    ingest_esco_occupations,
)

_DATA_PATH = "data/esco_occupations_en.csv"


class TestExtractCode:
    def test_extracts_uuid_from_uri(self):
        uri = "http://data.europa.eu/esco/occupation/14a21b3e-8d10-49a7-a7fb-b2e2e61ebb13"
        assert _extract_code(uri) == "14a21b3e-8d10-49a7-a7fb-b2e2e61ebb13"

    def test_extracts_code_from_different_uuid(self):
        uri = "http://data.europa.eu/esco/occupation/f1234567-abcd-1234-efgh-000000000001"
        assert _extract_code(uri) == "f1234567-abcd-1234-efgh-000000000001"

    def test_trailing_slash_stripped(self):
        uri = "http://data.europa.eu/esco/occupation/aaaa1111-0000-0000-0000-bbbbccccdddd/"
        assert _extract_code(uri) == "aaaa1111-0000-0000-0000-bbbbccccdddd"

    def test_non_empty_result(self):
        uri = "http://data.europa.eu/esco/occupation/some-code-here"
        result = _extract_code(uri)
        assert result and result.strip()


class TestDetermineSector:
    def test_isco_2411_gives_sector_2(self):
        assert _determine_sector("2411") == "2"

    def test_isco_1120_gives_sector_1(self):
        assert _determine_sector("1120") == "1"

    def test_isco_9321_gives_sector_9(self):
        assert _determine_sector("9321") == "9"

    def test_isco_3422_gives_sector_3(self):
        assert _determine_sector("3422") == "3"

    def test_handles_leading_whitespace(self):
        assert _determine_sector("  2411") == "2"

    def test_empty_isco_returns_zero_string(self):
        result = _determine_sector("")
        assert result == "0"


def test_esco_occupations_module_importable():
    assert callable(ingest_esco_occupations)
    assert callable(_extract_code)
    assert callable(_determine_sector)


@pytest.mark.skipif(
    not os.path.exists(_DATA_PATH),
    reason=f"ESCO occupations CSV not found at {_DATA_PATH}. "
           "Run: python -m world_of_taxanomy ingest esco_occupations",
)
def test_ingest_esco_occupations_from_real_file(db_pool):
    """Integration test: ingest ESCO occupations from downloaded CSV."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_esco_occupations(conn, path=_DATA_PATH)
            assert count >= 2900, f"Expected >= 2900 ESCO occupations, got {count}"
            assert count <= 4000, f"Expected <= 4000 ESCO occupations, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system "
                "WHERE id = 'esco_occupations'"
            )
            assert row is not None
            assert row["node_count"] == count

            # Spot-check: all nodes should be level=1, parent=None, is_leaf=True
            sample = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf "
                "FROM classification_node "
                "WHERE system_id = 'esco_occupations' "
                "LIMIT 1"
            )
            assert sample is not None
            assert sample["level"] == 1
            assert sample["parent_code"] is None
            assert sample["is_leaf"] is True

            # sector_code should be a single digit string
            sector_sample = await conn.fetchrow(
                "SELECT sector_code FROM classification_node "
                "WHERE system_id = 'esco_occupations' "
                "AND sector_code IS NOT NULL "
                "LIMIT 1"
            )
            if sector_sample:
                assert len(sector_sample["sector_code"]) == 1
                assert sector_sample["sector_code"].isdigit()

    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(
    not os.path.exists(_DATA_PATH),
    reason=f"ESCO occupations CSV not found at {_DATA_PATH}.",
)
def test_ingest_esco_occupations_idempotent(db_pool):
    """Running ingest twice returns the same count both times."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_esco_occupations(conn, path=_DATA_PATH)
            count2 = await ingest_esco_occupations(conn, path=_DATA_PATH)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
