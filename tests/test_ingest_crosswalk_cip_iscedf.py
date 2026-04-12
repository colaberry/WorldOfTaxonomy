"""Tests for CIP 2020 <-> ISCED-F 2013 crosswalk ingester.

RED tests - written before any implementation exists.

Source: Statistics Canada CIP 2016 / ISCED-F 2013 concordance (public domain)
  Locally downloaded as data/cip2016_iscedf.csv (encoding: latin-1)
  Columns: CIP Canada 2016 Code, CIP Canada 2016 Title, ISCED-F 2013 Code, ISCED-F 2013 Title

Match types:
  'exact'   - ISCED code has no asterisk
  'partial' - ISCED code ends with '*' (strip before inserting)

~1,809 rows; CIP codes filtered to those in cip_2020 DB;
ISCED codes filtered to those in iscedf_2013 DB.
~1,807 valid bidirectional pairs -> ~3,614 edges.
"""
import asyncio
import pytest
from pathlib import Path

from world_of_taxanomy.ingest.crosswalk_cip_iscedf import (
    ingest_crosswalk_cip_iscedf,
    _match_type,
)


def test_crosswalk_cip_iscedf_module_importable():
    """Function and helper are importable and callable."""
    assert callable(ingest_crosswalk_cip_iscedf)
    assert callable(_match_type)


class TestMatchType:
    def test_no_asterisk_is_exact(self):
        assert _match_type("0810") == "exact"

    def test_asterisk_is_partial(self):
        assert _match_type("0811*") == "partial"

    def test_stripped_code_no_asterisk_exact(self):
        assert _match_type("0110") == "exact"

    def test_another_asterisk_is_partial(self):
        assert _match_type("0111*") == "partial"


def test_ingest_crosswalk_cip_iscedf(db_pool):
    """Integration test - inserts bidirectional CIP 2020 <-> ISCED-F 2013 edges."""
    cw_path = Path("data/cip2016_iscedf.csv")
    cip_path = Path("data/cip_2020.csv")
    iscedf_path = Path("data/iscedf_2013.json")
    if not all(p.exists() for p in [cw_path, cip_path, iscedf_path]):
        pytest.skip("Download data files first")

    async def _run():
        from world_of_taxanomy.ingest.cip_2020 import ingest_cip_2020
        from world_of_taxanomy.ingest.iscedf_2013 import ingest_iscedf_2013
        async with db_pool.acquire() as conn:
            await ingest_cip_2020(conn, path=str(cip_path))
            await ingest_iscedf_2013(conn, path=str(iscedf_path))
            count = await ingest_crosswalk_cip_iscedf(conn, path=str(cw_path))
            # ~1807 valid pairs x 2 directions
            assert count >= 3000, f"Expected >= 3000 edges, got {count}"

            # Forward: CIP "01.0000" -> ISCED "0810" (exact match, no asterisk in source)
            fwd = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'cip_2020' AND source_code = '01.0000' "
                "AND target_system = 'iscedf_2013' AND target_code = '0810'"
            )
            assert fwd is not None, "Forward edge cip_2020:01.0000 -> iscedf_2013:0810 missing"
            assert fwd["match_type"] == "exact"

            # Reverse: ISCED "0810" -> CIP "01.0000"
            rev = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'iscedf_2013' AND source_code = '0810' "
                "AND target_system = 'cip_2020' AND target_code = '01.0000'"
            )
            assert rev is not None, "Reverse edge iscedf_2013:0810 -> cip_2020:01.0000 missing"
            assert rev["match_type"] == "exact"

            # Partial match: CIP "01.0101" -> ISCED "0811" (asterisk stripped, partial)
            partial = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'cip_2020' AND source_code = '01.0101' "
                "AND target_system = 'iscedf_2013' AND target_code = '0811'"
            )
            assert partial is not None, "Partial edge cip_2020:01.0101 -> iscedf_2013:0811 missing"
            assert partial["match_type"] == "partial"

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_cip_iscedf_idempotent(db_pool):
    """Running ingest twice returns consistent count."""
    cw_path = Path("data/cip2016_iscedf.csv")
    cip_path = Path("data/cip_2020.csv")
    iscedf_path = Path("data/iscedf_2013.json")
    if not all(p.exists() for p in [cw_path, cip_path, iscedf_path]):
        pytest.skip("Download data files first")

    async def _run():
        from world_of_taxanomy.ingest.cip_2020 import ingest_cip_2020
        from world_of_taxanomy.ingest.iscedf_2013 import ingest_iscedf_2013
        async with db_pool.acquire() as conn:
            await ingest_cip_2020(conn, path=str(cip_path))
            await ingest_iscedf_2013(conn, path=str(iscedf_path))
            count1 = await ingest_crosswalk_cip_iscedf(conn, path=str(cw_path))
            count2 = await ingest_crosswalk_cip_iscedf(conn, path=str(cw_path))
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())


def test_crosswalk_asterisk_codes_stripped(db_pool):
    """Asterisk suffix is stripped from ISCED codes before insertion."""
    cw_path = Path("data/cip2016_iscedf.csv")
    cip_path = Path("data/cip_2020.csv")
    iscedf_path = Path("data/iscedf_2013.json")
    if not all(p.exists() for p in [cw_path, cip_path, iscedf_path]):
        pytest.skip("Download data files first")

    async def _run():
        from world_of_taxanomy.ingest.cip_2020 import ingest_cip_2020
        from world_of_taxanomy.ingest.iscedf_2013 import ingest_iscedf_2013
        async with db_pool.acquire() as conn:
            await ingest_cip_2020(conn, path=str(cip_path))
            await ingest_iscedf_2013(conn, path=str(iscedf_path))
            await ingest_crosswalk_cip_iscedf(conn, path=str(cw_path))

            # No edge should have a target_code ending with '*'
            starred = await conn.fetchval(
                "SELECT COUNT(*) FROM equivalence "
                "WHERE (source_system = 'cip_2020' AND target_system = 'iscedf_2013' "
                "AND target_code LIKE '%*') "
                "OR (source_system = 'iscedf_2013' AND source_code LIKE '%*')"
            )
            assert starred == 0, f"Found {starred} rows with asterisk codes"

    asyncio.get_event_loop().run_until_complete(_run())
