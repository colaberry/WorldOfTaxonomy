"""Tests for world_of_taxonomy.mcp.http_dispatcher.

Each test exercises the dispatcher's request shape (HTTP method + path
+ params + body) using an httpx MockTransport. We do not depend on a
real WoT API; we just confirm the dispatcher would have made the
right call and parses the response cleanly.
"""

import asyncio
from typing import Optional, Tuple

import httpx
import pytest

from world_of_taxonomy.mcp.http_dispatcher import (
    DISPATCH_TABLE,
    dispatch_http,
    supported_tools,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def captured_request():
    """Returns (record_request, build_client). The record_request list
    holds (method, path, params, body) for each call captured by the
    mock transport. build_client returns a fresh client wired to a
    MockTransport that echoes back a fixed-shape JSON body."""
    record = []

    def build_client(response_body=None):
        if response_body is None:
            response_body = {"ok": True}

        def handler(req: httpx.Request) -> httpx.Response:
            record.append((
                req.method,
                req.url.path,
                dict(req.url.params),
                None if not req.content else __import__("json").loads(req.content),
            ))
            return httpx.Response(200, json=response_body)

        return httpx.AsyncClient(
            base_url="http://test",
            transport=httpx.MockTransport(handler),
        )

    return record, build_client


# Each test is a (tool_name, args, expected_method, expected_path_substring,
# expected_param_keys, expected_body_keys-or-None) tuple. Keeps the table
# tight and the assertions uniform.

DISPATCH_CASES: list[Tuple[str, dict, str, str, set, Optional[set]]] = [
    ("list_classification_systems", {}, "GET", "/api/v1/systems", set(), None),
    ("list_classification_systems", {"country_code": "DE"},
     "GET", "/api/v1/systems", {"country"}, None),
    ("search_systems", {"query": "naics"},
     "GET", "/api/v1/systems", {"q"}, None),
    ("get_industry", {"system_id": "naics_2022", "code": "6211"},
     "GET", "/api/v1/systems/naics_2022/nodes/6211", set(), None),
    ("browse_children", {"system_id": "naics_2022", "parent_code": "62"},
     "GET", "/api/v1/systems/naics_2022/nodes/62/children", set(), None),
    ("get_ancestors", {"system_id": "naics_2022", "code": "62111"},
     "GET", "/api/v1/systems/naics_2022/nodes/62111/ancestors", set(), None),
    ("get_equivalences", {"system_id": "naics_2022", "code": "6211"},
     "GET", "/api/v1/systems/naics_2022/nodes/6211/equivalences", set(), None),
    ("translate_code",
     {"source_system": "naics_2022", "source_code": "6211",
      "target_system": "isic_rev4"},
     "GET", "/api/v1/systems/naics_2022/nodes/6211/equivalences",
     {"target_system"}, None),
    ("translate_across_all_systems",
     {"system_id": "naics_2022", "code": "6211"},
     "GET", "/api/v1/systems/naics_2022/nodes/6211/equivalences",
     set(), None),
    ("get_sector_overview", {"system_id": "naics_2022"},
     "GET", "/api/v1/systems/naics_2022", set(), None),
    ("search_classifications",
     {"query": "physician", "system_id": "naics_2022", "limit": 5},
     "GET", "/api/v1/search", {"q", "system_id", "limit"}, None),
    ("search_classifications",
     {"query": "physician", "countries": ["US", "CA"]},
     "GET", "/api/v1/search", {"q", "countries"}, None),
    ("find_by_keyword_all_systems",
     {"query": "doctor", "limit_per_system": 10},
     "GET", "/api/v1/search", {"q", "grouped", "limit"}, None),
    ("explore_industry_tree",
     {"query": "fintech", "system_id": "naics_2022"},
     "GET", "/api/v1/search", {"q", "context", "system_id"}, None),
    ("compare_sector",
     {"system_id_a": "naics_2022", "system_id_b": "isic_rev4"},
     "GET", "/api/v1/compare", {"a", "b"}, None),
    ("get_system_diff",
     {"system_id_a": "naics_2022", "system_id_b": "isic_rev4"},
     "GET", "/api/v1/diff", {"a", "b"}, None),
    ("get_siblings",
     {"system_id": "naics_2022", "code": "6211"},
     "GET", "/api/v1/systems/naics_2022/nodes/6211/siblings", set(), None),
    ("get_subtree_summary",
     {"system_id": "naics_2022", "code": "62"},
     "GET", "/api/v1/systems/naics_2022/nodes/62/subtree", set(), None),
    ("resolve_ambiguous_code", {"code": "0111"},
     "GET", "/api/v1/nodes/0111", set(), None),
    ("get_crosswalk_coverage", {"system_id": "naics_2022"},
     "GET", "/api/v1/equivalences/stats", {"system_id"}, None),
    ("get_leaf_count", {},
     "GET", "/api/v1/systems/stats", set(), None),
    ("get_region_mapping", {},
     "GET", "/api/v1/systems", {"group_by"}, None),
    ("get_country_taxonomy_profile", {"country_code": "DE"},
     "GET", "/api/v1/countries/DE", set(), None),
    ("classify_business",
     {"text": "soybean farm in iowa", "limit": 3},
     "POST", "/api/v1/classify", set(), {"text", "limit"}),
]


@pytest.mark.cli
@pytest.mark.parametrize("case", DISPATCH_CASES, ids=lambda c: c[0])
def test_dispatcher_request_shape(captured_request, case):
    tool, args, exp_method, exp_path, exp_params, exp_body_keys = case
    record, build_client = captured_request

    async def go():
        async with build_client() as c:
            await dispatch_http(c, tool, args)

    _run(go())
    assert len(record) == 1, f"{tool}: expected 1 request, got {len(record)}"
    method, path, params, body = record[0]
    assert method == exp_method, f"{tool}: method mismatch"
    assert path == exp_path, f"{tool}: path mismatch ({path})"
    assert exp_params == set(params.keys()), \
        f"{tool}: params mismatch (got {set(params.keys())}, want {exp_params})"
    if exp_body_keys is None:
        assert body is None
    else:
        assert set(body.keys()) == exp_body_keys


@pytest.mark.cli
class TestDispatcherErrors:
    def test_describe_match_types_returns_static_payload_no_http(
            self, captured_request):
        record, build_client = captured_request

        async def go():
            async with build_client() as c:
                return await dispatch_http(c, "describe_match_types", {})

        result = _run(go())
        assert "match_types" in result and "edge_kinds" in result
        assert record == []  # no HTTP call made

    def test_unknown_tool_raises_NotImplementedError(self, captured_request):
        _, build_client = captured_request

        async def go():
            async with build_client() as c:
                await dispatch_http(c, "tool_that_does_not_exist", {})

        with pytest.raises(NotImplementedError, match="no HTTP-mode dispatcher"):
            _run(go())

    def test_known_unwired_tool_has_pointed_message(self, captured_request):
        _, build_client = captured_request

        async def go():
            async with build_client() as c:
                await dispatch_http(c, "list_crosswalks_by_kind",
                                    {"edge_kind": "standard_standard"})

        with pytest.raises(NotImplementedError, match="not yet wired in HTTP mode"):
            _run(go())

    def test_4xx_propagates_as_HTTPStatusError(self, captured_request):
        def err_handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"detail": {"error": "missing_api_key"}})

        async def go():
            async with httpx.AsyncClient(
                base_url="http://test", transport=httpx.MockTransport(err_handler),
            ) as c:
                await dispatch_http(c, "get_industry",
                                    {"system_id": "naics_2022", "code": "6211"})

        with pytest.raises(httpx.HTTPStatusError):
            _run(go())


@pytest.mark.cli
def test_supported_tools_covers_dispatch_table():
    """`supported_tools()` must list every entry in DISPATCH_TABLE
    plus the static-payload tools, so the operator can introspect
    which MCP tools are HTTP-callable."""
    s = set(supported_tools())
    for tool in DISPATCH_TABLE:
        assert tool in s
    assert "describe_match_types" in s
