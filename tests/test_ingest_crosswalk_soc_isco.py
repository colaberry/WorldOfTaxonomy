"""Tests for SOC 2018 <-> ISCO-08 crosswalk ingester.

RED tests - written before any implementation exists.

Source: SOC 2010 <-> ISCO-08 correspondence (danielruss/codingsystems)
  https://danielruss.github.io/codingsystems/soc2010_isco2008.csv

SOC codes are filtered to those present in our soc_2018 system.
Match type is 'broad' (SOC 2010 vs SOC 2018 version difference).
"""
import asyncio
import pytest
from pathlib import Path

from world_of_taxanomy.ingest.crosswalk_soc_isco import ingest_crosswalk_soc_isco


def test_crosswalk_soc_isco_module_importable():
    """Function is importable and callable."""
    assert callable(ingest_crosswalk_soc_isco)


def test_ingest_crosswalk_soc_isco(db_pool):
    """Integration test - inserts bidirectional SOC 2018 <-> ISCO-08 edges."""
    data_path = Path("data/soc2010_isco08.csv")
    if not data_path.exists():
        pytest.skip(
            "Download data/soc2010_isco08.csv first: "
            "https://danielruss.github.io/codingsystems/soc2010_isco2008.csv"
        )

    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_crosswalk_soc_isco(conn, path=str(data_path))
            # ~992 pairs x 2 = ~1984 edges (filtered to codes in our SOC 2018 DB)
            assert count >= 1800, f"Expected >= 1800 edges, got {count}"

            # Check forward edge: SOC "11-1011" -> ISCO "1120"
            fwd = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'soc_2018' AND source_code = '11-1011' "
                "AND target_system = 'isco_08' AND target_code = '1120'"
            )
            assert fwd is not None, "Forward edge soc_2018:11-1011 -> isco_08:1120 missing"
            assert fwd["match_type"] == "broad"

            # Check reverse edge: ISCO "1120" -> SOC "11-1011"
            rev = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'isco_08' AND source_code = '1120' "
                "AND target_system = 'soc_2018' AND target_code = '11-1011'"
            )
            assert rev is not None, "Reverse edge isco_08:1120 -> soc_2018:11-1011 missing"
            assert rev["match_type"] == "broad"

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_soc_isco_idempotent(db_pool):
    """Running ingest twice does not raise and returns consistent count."""
    data_path = Path("data/soc2010_isco08.csv")
    if not data_path.exists():
        pytest.skip("Download data/soc2010_isco08.csv first")

    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_crosswalk_soc_isco(conn, path=str(data_path))
            count2 = await ingest_crosswalk_soc_isco(conn, path=str(data_path))
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())


def test_crosswalk_excludes_codes_not_in_soc2018(db_pool):
    """SOC codes not present in our soc_2018 system are not inserted."""
    data_path = Path("data/soc2010_isco08.csv")
    if not data_path.exists():
        pytest.skip("Download data/soc2010_isco08.csv first")

    async def _run():
        async with db_pool.acquire() as conn:
            await ingest_crosswalk_soc_isco(conn, path=str(data_path))
            # Count edges whose source_code is not in our soc_2018 system
            orphans = await conn.fetchval(
                """SELECT COUNT(*) FROM equivalence e
                   WHERE e.source_system = 'soc_2018'
                   AND NOT EXISTS (
                       SELECT 1 FROM classification_node n
                       WHERE n.system_id = 'soc_2018' AND n.code = e.source_code
                   )"""
            )
            assert orphans == 0, f"Found {orphans} edges with SOC codes not in soc_2018"

    asyncio.get_event_loop().run_until_complete(_run())
