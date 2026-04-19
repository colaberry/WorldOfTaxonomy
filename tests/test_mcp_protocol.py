"""Tests for MCP JSON-RPC protocol handling.

TDD RED phase: these tests define the contract for the MCP protocol layer -
tool listing, tool calling, resource listing, and resource reading.
"""

import asyncio
import json
import pytest

from world_of_taxonomy.mcp.protocol import (
    build_tools_list,
    build_resources_list,
    handle_jsonrpc_request,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── tools/list ────────────────────────────────────────────────


def test_tools_list_returns_24_tools():
    tools = build_tools_list()
    assert len(tools) == 24
    names = {t["name"] for t in tools}
    assert names == {
        "list_classification_systems",
        "get_industry",
        "browse_children",
        "get_ancestors",
        "search_classifications",
        "get_equivalences",
        "translate_code",
        "get_sector_overview",
        "translate_across_all_systems",
        "compare_sector",
        "find_by_keyword_all_systems",
        "get_crosswalk_coverage",
        "list_crosswalks_by_kind",
        "get_system_diff",
        "get_siblings",
        "get_subtree_summary",
        "resolve_ambiguous_code",
        "get_leaf_count",
        "get_region_mapping",
        "describe_match_types",
        "explore_industry_tree",
        "get_audit_report",
        "get_country_taxonomy_profile",
        "classify_business",
    }


def test_tools_have_schema():
    tools = build_tools_list()
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        schema = tool["inputSchema"]
        assert schema["type"] == "object"


# ── resources/list ────────────────────────────────────────────


def test_resources_list():
    resources = build_resources_list()
    assert len(resources) == 13  # 2 core + 11 wiki pages
    uris = {r["uri"] for r in resources}
    assert "taxonomy://systems" in uris
    assert "taxonomy://wiki/getting-started" in uris


# ── JSON-RPC handling ─────────────────────────────────────────


def test_handle_initialize():
    async def _test():
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            },
        }
        response = await handle_jsonrpc_request(request, conn=None)
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "WorldOfTaxonomy"
        assert "tools" in response["result"]["capabilities"]
        assert "resources" in response["result"]["capabilities"]
    _run(_test())


def test_handle_tools_list():
    async def _test():
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
        }
        response = await handle_jsonrpc_request(request, conn=None)
        assert response["id"] == 2
        assert "result" in response
        assert len(response["result"]["tools"]) == 24
    _run(_test())


def test_handle_tools_call(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_classifications",
                    "arguments": {"query": "physician"},
                },
            }
            response = await handle_jsonrpc_request(request, conn=conn)
            assert response["id"] == 3
            assert "result" in response
            content = response["result"]["content"]
            assert len(content) == 1
            assert content[0]["type"] == "text"
            # Content should be valid JSON
            data = json.loads(content[0]["text"])
            assert isinstance(data, list)
    _run(_test())


def test_handle_tools_call_unknown_tool(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {},
                },
            }
            response = await handle_jsonrpc_request(request, conn=conn)
            assert response["id"] == 4
            assert "error" in response
    _run(_test())


def test_handle_resources_list():
    async def _test():
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "resources/list",
        }
        response = await handle_jsonrpc_request(request, conn=None)
        assert response["id"] == 5
        assert "result" in response
        assert len(response["result"]["resources"]) == 13  # 2 core + 11 wiki pages
    _run(_test())


def test_handle_resources_read(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            request = {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "resources/read",
                "params": {"uri": "taxonomy://systems"},
            }
            response = await handle_jsonrpc_request(request, conn=conn)
            assert response["id"] == 6
            assert "result" in response
            contents = response["result"]["contents"]
            assert len(contents) == 1
            data = json.loads(contents[0]["text"])
            assert isinstance(data, list)
    _run(_test())


def test_handle_unknown_method():
    async def _test():
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "unknown/method",
        }
        response = await handle_jsonrpc_request(request, conn=None)
        assert response["id"] == 7
        assert "error" in response
    _run(_test())
