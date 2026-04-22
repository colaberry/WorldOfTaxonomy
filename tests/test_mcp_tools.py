"""Tests for MCP server tool handlers.

TDD RED phase: these tests define the contract for each MCP tool.
Tools reuse the query layer, so we test the handler wrappers that
format results for MCP clients.
"""

import asyncio
import pytest

from world_of_taxonomy.mcp.handlers import (
    handle_list_classification_systems,
    handle_get_industry,
    handle_browse_children,
    handle_get_ancestors,
    handle_search_classifications,
    handle_search_systems,
    handle_get_equivalences,
    handle_translate_code,
    handle_get_sector_overview,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Tool: list_classification_systems ─────────────────────────


def test_list_systems(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_list_classification_systems(conn, {})
            assert isinstance(result, list)
            assert len(result) >= 2
            ids = {s["id"] for s in result}
            assert "naics_2022" in ids
            assert "isic_rev4" in ids
            # Each system should have key fields
            for s in result:
                assert "id" in s
                assert "name" in s
                assert "node_count" in s
    _run(_test())


def test_list_systems_filtered_by_country(db_pool):
    """Passing country_code returns only systems applicable to that country."""
    async def _test():
        async with db_pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO country_system_link (country_code, system_id, relevance)
                   VALUES ($1, $2, $3)
                   ON CONFLICT DO NOTHING""",
                [
                    ("DE", "isic_rev4", "recommended"),
                    ("US", "naics_2022", "official"),
                    ("US", "isic_rev4", "recommended"),
                ],
            )
            result = await handle_list_classification_systems(
                conn, {"country_code": "US"}
            )
            ids = {s["id"] for s in result}
            assert "naics_2022" in ids
            assert "isic_rev4" in ids

            de_result = await handle_list_classification_systems(
                conn, {"country_code": "DE"}
            )
            de_ids = {s["id"] for s in de_result}
            assert "isic_rev4" in de_ids
            assert "naics_2022" not in de_ids
    _run(_test())


# ── Tool: get_industry ────────────────────────────────────────


def test_get_industry(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_industry(conn, {
                "system_id": "naics_2022",
                "code": "62",
            })
            assert result["code"] == "62"
            assert result["system_id"] == "naics_2022"
            assert "title" in result
    _run(_test())


def test_get_industry_not_found(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_industry(conn, {
                "system_id": "naics_2022",
                "code": "99999",
            })
            assert "error" in result
    _run(_test())


# ── Tool: browse_children ────────────────────────────────────


def test_browse_children(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_browse_children(conn, {
                "system_id": "naics_2022",
                "parent_code": "62",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
            for child in result:
                assert "code" in child
                assert "title" in child
    _run(_test())


# ── Tool: get_ancestors ──────────────────────────────────────


def test_get_ancestors(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_ancestors(conn, {
                "system_id": "naics_2022",
                "code": "621",
            })
            assert isinstance(result, list)
            assert len(result) >= 2
            # First should be root, last should be the node itself
            assert result[-1]["code"] == "621"
    _run(_test())


# ── Tool: search_classifications ─────────────────────────────


def test_search_classifications(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_search_classifications(conn, {
                "query": "physician",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
    _run(_test())


def test_search_with_system_filter(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_search_classifications(conn, {
                "query": "health",
                "system_id": "naics_2022",
            })
            for item in result:
                assert item["system_id"] == "naics_2022"
    _run(_test())


def test_search_with_limit(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_search_classifications(conn, {
                "query": "farming",
                "limit": 2,
            })
            assert len(result) <= 2
    _run(_test())


# ── Tool: get_equivalences ───────────────────────────────────


def test_get_equivalences(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_equivalences(conn, {
                "system_id": "naics_2022",
                "code": "6211",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
            assert any(e["target_system"] == "isic_rev4" for e in result)
    _run(_test())


# ── Tool: translate_code ─────────────────────────────────────


def test_translate_code(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_translate_code(conn, {
                "source_system": "naics_2022",
                "source_code": "6211",
                "target_system": "isic_rev4",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
            assert result[0]["target_code"] == "8620"
    _run(_test())


# ── Tool: search_systems ─────────────────────────────────────


def test_search_systems_matches_by_name(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_search_systems(conn, {"query": "NAICS"})
            assert isinstance(result, list)
            ids = {s["id"] for s in result}
            assert "naics_2022" in ids
            for s in result:
                assert "id" in s
                assert "name" in s
    _run(_test())


def test_search_systems_case_insensitive(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_search_systems(conn, {"query": "naics"})
            ids = {s["id"] for s in result}
            assert "naics_2022" in ids
    _run(_test())


def test_search_systems_empty_query(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_search_systems(conn, {"query": ""})
            assert result == []
    _run(_test())


# ── Tool: get_sector_overview ────────────────────────────────


def test_get_sector_overview(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_sector_overview(conn, {
                "system_id": "naics_2022",
            })
            assert isinstance(result, list)
            assert len(result) >= 1
            for sector in result:
                assert "code" in sector
                assert "title" in sector
    _run(_test())
