"""Tests for classification_node.description backfill utilities.

The backfill path is used by per-system scripts that re-parse source
files (Census, Eurostat, WHO, ...) and fill the description column
without rewriting the hierarchy. Only NULL/empty rows are updated, so
re-running is a no-op on any node that already has a description.
"""

import asyncio

from world_of_taxonomy.ingest.descriptions import apply_descriptions


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_apply_descriptions_fills_null_rows(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            before = await conn.fetchval(
                "SELECT description FROM classification_node "
                "WHERE system_id = 'naics_2022' AND code = '11'"
            )
            assert before is None

            updated = await apply_descriptions(
                conn,
                "naics_2022",
                {"11": "Agriculture sector description."},
            )
            assert updated == 1

            after = await conn.fetchval(
                "SELECT description FROM classification_node "
                "WHERE system_id = 'naics_2022' AND code = '11'"
            )
            assert after == "Agriculture sector description."

    _run(_test())


def test_apply_descriptions_preserves_existing(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            # Code 6211 is pre-seeded with a description
            original = await conn.fetchval(
                "SELECT description FROM classification_node "
                "WHERE system_id = 'naics_2022' AND code = '6211'"
            )
            assert original == "Establishments with M.D. or D.O. degrees"

            updated = await apply_descriptions(
                conn,
                "naics_2022",
                {"6211": "NEW DESCRIPTION"},
            )
            assert updated == 0

            after = await conn.fetchval(
                "SELECT description FROM classification_node "
                "WHERE system_id = 'naics_2022' AND code = '6211'"
            )
            assert after == original

    _run(_test())


def test_apply_descriptions_strips_and_skips_empty(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            updated = await apply_descriptions(
                conn,
                "naics_2022",
                {
                    "62": "  Health care sector.  ",
                    "31-33": "",
                    "111": None,
                },
            )
            assert updated == 1

            val = await conn.fetchval(
                "SELECT description FROM classification_node "
                "WHERE system_id = 'naics_2022' AND code = '62'"
            )
            assert val == "Health care sector."

            for code in ("31-33", "111"):
                val = await conn.fetchval(
                    "SELECT description FROM classification_node "
                    "WHERE system_id = 'naics_2022' AND code = $1",
                    code,
                )
                assert val is None

    _run(_test())


def test_apply_descriptions_ignores_unknown_codes(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            updated = await apply_descriptions(
                conn,
                "naics_2022",
                {"99999": "Code that does not exist in seed."},
            )
            assert updated == 0

    _run(_test())
