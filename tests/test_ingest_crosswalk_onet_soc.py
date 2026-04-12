"""Tests for O*NET-SOC <-> SOC 2018 crosswalk ingester.

RED tests - written before any implementation exists.

O*NET-SOC base occupations (codes ending '.00') map 1:1 to SOC 2018
detailed occupations. The O*NET code '11-1011.00' corresponds exactly to
SOC 2018 code '11-1011'.

This crosswalk derives the mapping by stripping '.00' from the O*NET code
to produce the SOC code, then verifying both codes exist in their systems.

Edge semantics:
  onet_soc -> soc_2018: match_type='exact' (same occupation, different scheme)
  soc_2018 -> onet_soc: match_type='exact'

Source: derived from onet_soc data (data file already downloaded)
~867 pairs -> ~1,734 bidirectional edges
"""
import asyncio
import os
import pytest

from world_of_taxanomy.ingest.crosswalk_onet_soc import ingest_crosswalk_onet_soc

_ONET_PATH = "data/onet_occupation_data.txt"


def test_crosswalk_onet_soc_module_importable():
    assert callable(ingest_crosswalk_onet_soc)


@pytest.mark.skipif(
    not os.path.exists(_ONET_PATH),
    reason=f"O*NET data not found at {_ONET_PATH}. "
           "Run: python -m world_of_taxanomy ingest onet_soc",
)
def test_ingest_crosswalk_onet_soc(db_pool):
    """Integration test: creates bidirectional O*NET <-> SOC 2018 edges."""
    async def _run():
        from world_of_taxanomy.ingest.onet_soc import ingest_onet_soc
        from world_of_taxanomy.ingest.soc_2018 import ingest_soc_2018
        async with db_pool.acquire() as conn:
            await ingest_onet_soc(conn, path=_ONET_PATH)
            await ingest_soc_2018(conn)

            count = await ingest_crosswalk_onet_soc(conn, path=_ONET_PATH)
            # ~867 pairs x 2 = ~1,734 edges
            assert count >= 1600, f"Expected >= 1600 edges, got {count}"
            assert count <= 2000, f"Expected <= 2000 edges, got {count}"

            # Edges should be exact match type
            fwd_sample = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'onet_soc' "
                "AND target_system = 'soc_2018' "
                "LIMIT 1"
            )
            assert fwd_sample is not None
            assert fwd_sample["match_type"] == "exact"

            rev_sample = await conn.fetchrow(
                "SELECT match_type FROM equivalence "
                "WHERE source_system = 'soc_2018' "
                "AND target_system = 'onet_soc' "
                "LIMIT 1"
            )
            assert rev_sample is not None
            assert rev_sample["match_type"] == "exact"

    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(
    not os.path.exists(_ONET_PATH),
    reason=f"O*NET data not found at {_ONET_PATH}.",
)
def test_ingest_crosswalk_onet_soc_idempotent(db_pool):
    """Running ingest twice returns consistent count."""
    async def _run():
        from world_of_taxanomy.ingest.onet_soc import ingest_onet_soc
        from world_of_taxanomy.ingest.soc_2018 import ingest_soc_2018
        async with db_pool.acquire() as conn:
            await ingest_onet_soc(conn, path=_ONET_PATH)
            await ingest_soc_2018(conn)
            count1 = await ingest_crosswalk_onet_soc(conn, path=_ONET_PATH)
            count2 = await ingest_crosswalk_onet_soc(conn, path=_ONET_PATH)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
