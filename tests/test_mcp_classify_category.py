"""MCP contract tests for domain/standard category split.

Every system + node dict that crosses the MCP wire carries a 'category'
field. The classify_business tool returns domain_matches + standard_matches
and intentionally drops the legacy flat 'matches' key.
"""

import asyncio

from world_of_taxonomy.mcp.handlers import (
    handle_list_classification_systems,
    handle_search_classifications,
    handle_get_industry,
    handle_classify_business,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_list_systems_carries_category(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_list_classification_systems(conn, {})
            assert len(result) > 0
            for sys in result:
                assert "category" in sys
                assert sys["category"] in ("domain", "standard")
                if sys["id"].startswith("domain_"):
                    assert sys["category"] == "domain"
                else:
                    assert sys["category"] == "standard"
    _run(_test())


def test_search_results_carry_category(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            results = await handle_search_classifications(conn, {"query": "health"})
            for r in results:
                assert "category" in r
                assert r["category"] in ("domain", "standard")
    _run(_test())


def test_get_industry_carries_category(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_get_industry(conn, {
                "system_id": "naics_2022",
                "code": "62",
            })
            assert result.get("category") == "standard"
    _run(_test())


def test_classify_business_returns_split_matches(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_classify_business(conn, {"text": "hospital"})
            # Legacy flat key must be absent.
            assert "matches" not in result
            assert "domain_matches" in result
            assert "standard_matches" in result
            assert isinstance(result["domain_matches"], list)
            assert isinstance(result["standard_matches"], list)
            for m in result["domain_matches"]:
                assert m["system_id"].startswith("domain_")
                assert m["category"] == "domain"
            for m in result["standard_matches"]:
                assert not m["system_id"].startswith("domain_")
                assert m["category"] == "standard"
    _run(_test())


def test_classify_business_rejects_short_input(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            result = await handle_classify_business(conn, {"text": "a"})
            assert "error" in result
    _run(_test())
