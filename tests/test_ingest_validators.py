"""Tests for world_of_taxonomy.ingest.validators."""

import asyncio

import pytest

from world_of_taxonomy.ingest.validators import (
    ValidationError,
    check_no_duplicate_codes,
    check_no_orphaned_parents,
    check_row_count,
    validate_system,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_check_row_count_within_bounds(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            count = await check_row_count(
                conn, "naics_2022", minimum=5, maximum=50
            )
            assert count == 10

    _run(_test())


def test_check_row_count_below_minimum_raises(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            with pytest.raises(ValidationError, match="at least 100"):
                await check_row_count(conn, "naics_2022", minimum=100)

    _run(_test())


def test_check_row_count_above_maximum_raises(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            with pytest.raises(ValidationError, match="at most 5"):
                await check_row_count(conn, "naics_2022", maximum=5)

    _run(_test())


def test_check_no_duplicate_codes_passes_clean_data(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            await check_no_duplicate_codes(conn, "naics_2022")

    _run(_test())


def test_check_no_orphaned_parents_passes_clean_data(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            await check_no_orphaned_parents(conn, "naics_2022")

    _run(_test())


def test_check_no_orphaned_parents_detects_missing_parent(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO classification_node
                    (system_id, code, title, level, parent_code, sector_code,
                     is_leaf, seq_order)
                VALUES ('naics_2022', '999999', 'Orphan', 5, '99999', '99',
                        TRUE, 999)
                """
            )
            try:
                with pytest.raises(ValidationError, match="missing parent"):
                    await check_no_orphaned_parents(conn, "naics_2022")
            finally:
                await conn.execute(
                    "DELETE FROM classification_node "
                    "WHERE system_id = 'naics_2022' AND code = '999999'"
                )

    _run(_test())


def test_validate_system_returns_report_on_success(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            report = await validate_system(
                conn, "naics_2022", expected_min=5, expected_max=50
            )
            assert report.ok
            assert report.node_count == 10
            assert report.errors == []

    _run(_test())


def test_validate_system_raises_by_default(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            with pytest.raises(ValidationError):
                await validate_system(conn, "naics_2022", expected_min=1000)

    _run(_test())


def test_validate_system_captures_error_when_not_raising(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            report = await validate_system(
                conn,
                "naics_2022",
                expected_min=1000,
                raise_on_error=False,
            )
            assert not report.ok
            assert len(report.errors) == 1
            assert "at least 1000" in report.errors[0]

    _run(_test())
