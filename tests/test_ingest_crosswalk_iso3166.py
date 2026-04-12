"""Tests for ISO 3166 crosswalk ingester.

RED tests - written before any implementation exists.

Links iso_3166_1 country nodes to iso_3166_2 country stub nodes.
Each alpha-2 country code present in both systems gets a bidirectional
exact equivalence edge.

~249 countries x 2 directions = ~498 edges.
"""
import pytest
from world_of_taxanomy.ingest.crosswalk_iso3166 import (
    ingest_crosswalk_iso3166,
)


def test_crosswalk_iso3166_module_importable():
    """The module exists and is importable."""
    from world_of_taxanomy.ingest import crosswalk_iso3166  # noqa: F401


def test_ingest_crosswalk_iso3166(db_pool):
    """Integration test - links iso_3166_1 and iso_3166_2 countries."""
    import asyncio
    from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1
    from world_of_taxanomy.ingest.iso3166_2 import ingest_iso3166_2

    async def _run():
        async with db_pool.acquire() as conn:
            # Must ingest both systems first
            await ingest_iso3166_1(conn)
            await ingest_iso3166_2(conn)

            edge_count = await ingest_crosswalk_iso3166(conn)

            # Should have at least 400 edges (249 countries x 2 directions)
            assert edge_count >= 400, f"Expected >= 400 edges, got {edge_count}"

            # US should be linked in both directions
            us_fwd = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'iso_3166_1'
                     AND source_code = 'US'
                     AND target_system = 'iso_3166_2'
                     AND target_code = 'US'"""
            )
            assert us_fwd is not None, "US: iso_3166_1 -> iso_3166_2 edge missing"
            assert us_fwd["match_type"] == "exact"

            us_rev = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'iso_3166_2'
                     AND source_code = 'US'
                     AND target_system = 'iso_3166_1'
                     AND target_code = 'US'"""
            )
            assert us_rev is not None, "US: iso_3166_2 -> iso_3166_1 edge missing"

            # DE should also be linked
            de = await conn.fetchrow(
                """SELECT * FROM equivalence
                   WHERE source_system = 'iso_3166_1'
                     AND source_code = 'DE'
                     AND target_system = 'iso_3166_2'"""
            )
            assert de is not None, "DE crosswalk edge missing"

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_crosswalk_iso3166_idempotent(db_pool):
    """Running the crosswalk twice does not create duplicate edges."""
    import asyncio
    from world_of_taxanomy.ingest.iso3166_1 import ingest_iso3166_1
    from world_of_taxanomy.ingest.iso3166_2 import ingest_iso3166_2

    async def _run():
        async with db_pool.acquire() as conn:
            await ingest_iso3166_1(conn)
            await ingest_iso3166_2(conn)
            count1 = await ingest_crosswalk_iso3166(conn)
            count2 = await ingest_crosswalk_iso3166(conn)
            assert count1 == count2, "Second run changed edge count - not idempotent"

    asyncio.get_event_loop().run_until_complete(_run())
