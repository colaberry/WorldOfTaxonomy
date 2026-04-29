"""Dispatch MCP tool calls over HTTP to the WorldOfTaxonomy REST API.

The MCP server has two modes:

  - DB mode (current behavior): each tool handler holds an asyncpg
    connection and queries Postgres directly. Used in development
    when DATABASE_URL is set.
  - HTTP mode: each tool call is translated into an HTTP request
    against `wot.aixcelerator.ai`, authenticated with the user's
    API key. Used by the published `worldoftaxonomy-mcp` PyPI
    package, where end users do not have a database.

This module is the HTTP-mode dispatcher. Each tool name maps to a
small function that returns `(method, path, query_params, json_body)`
for the REST call. `dispatch_http` runs the request and returns the
response body. The result shape is whatever the REST handler returns
(typically the same Pydantic model that backs the equivalent MCP
tool's DB-mode handler), so the LLM consumer sees comparable JSON in
either mode.

Tools that have no clean single-endpoint mapping raise
`NotImplementedError` with a pointer at the REST endpoint that would
need to be added; the operator can run the server in DB mode while
those land.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

import httpx


# ----- per-tool dispatchers --------------------------------------------------

def _list_systems(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    params: Dict[str, Any] = {}
    if args.get("country_code"):
        params["country"] = args["country_code"]
    return ("GET", "/api/v1/systems", params, None)


def _search_systems(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", "/api/v1/systems", {"q": args["query"]}, None)


def _get_industry(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", f"/api/v1/systems/{args['system_id']}/nodes/{args['code']}", {}, None)


def _browse_children(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET",
            f"/api/v1/systems/{args['system_id']}/nodes/{args['parent_code']}/children",
            {}, None)


def _get_ancestors(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET",
            f"/api/v1/systems/{args['system_id']}/nodes/{args['code']}/ancestors",
            {}, None)


def _get_equivalences(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET",
            f"/api/v1/systems/{args['system_id']}/nodes/{args['code']}/equivalences",
            {}, None)


def _translate_code(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    # Reuses the equivalences endpoint; the caller filters to target_system
    # client-side from the response. Cleaner than adding a /translate route.
    return ("GET",
            f"/api/v1/systems/{args['source_system']}/nodes/{args['source_code']}/equivalences",
            {"target_system": args["target_system"]}, None)


def _translate_across_all_systems(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET",
            f"/api/v1/systems/{args['system_id']}/nodes/{args['code']}/equivalences",
            {}, None)


def _get_sector_overview(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    # /systems/{id} returns SystemDetailResponse which includes top-level roots.
    return ("GET", f"/api/v1/systems/{args['system_id']}", {}, None)


def _search_classifications(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    params: Dict[str, Any] = {"q": args["query"]}
    if args.get("system_id"):
        params["system_id"] = args["system_id"]
    if args.get("system_ids"):
        params["system_ids"] = ",".join(args["system_ids"])
    if args.get("countries"):
        params["countries"] = ",".join(args["countries"])
    if args.get("limit") is not None:
        params["limit"] = args["limit"]
    return ("GET", "/api/v1/search", params, None)


def _find_by_keyword_all_systems(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    params: Dict[str, Any] = {"q": args["query"], "grouped": "true"}
    if args.get("limit_per_system") is not None:
        params["limit"] = args["limit_per_system"]
    return ("GET", "/api/v1/search", params, None)


def _explore_industry_tree(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    params: Dict[str, Any] = {"q": args["query"], "context": "true"}
    if args.get("system_id"):
        params["system_id"] = args["system_id"]
    if args.get("limit") is not None:
        params["limit"] = args["limit"]
    return ("GET", "/api/v1/search", params, None)


def _compare_sector(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", "/api/v1/compare",
            {"a": args["system_id_a"], "b": args["system_id_b"]}, None)


def _get_system_diff(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", "/api/v1/diff",
            {"a": args["system_id_a"], "b": args["system_id_b"]}, None)


def _get_siblings(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET",
            f"/api/v1/systems/{args['system_id']}/nodes/{args['code']}/siblings",
            {}, None)


def _get_subtree_summary(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET",
            f"/api/v1/systems/{args['system_id']}/nodes/{args['code']}/subtree",
            {}, None)


def _resolve_ambiguous_code(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", f"/api/v1/nodes/{args['code']}", {}, None)


def _get_crosswalk_coverage(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    params: Dict[str, Any] = {}
    if args.get("system_id"):
        params["system_id"] = args["system_id"]
    return ("GET", "/api/v1/equivalences/stats", params, None)


def _get_leaf_count(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    params: Dict[str, Any] = {}
    if args.get("system_id"):
        params["system_id"] = args["system_id"]
    return ("GET", "/api/v1/systems/stats", params, None)


def _get_region_mapping(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", "/api/v1/systems", {"group_by": "region"}, None)


def _get_country_taxonomy_profile(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    return ("GET", f"/api/v1/countries/{args['country_code']}", {}, None)


def _classify_business(args: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
    body: Dict[str, Any] = {"text": args["text"]}
    if args.get("systems"):
        body["systems"] = args["systems"]
    if args.get("countries"):
        body["countries"] = args["countries"]
    if args.get("limit") is not None:
        body["limit"] = args["limit"]
    return ("POST", "/api/v1/classify", {}, body)


# Tools that produce a fixed payload locally without hitting the API.
# They are computed in `dispatch_http` itself before any network call.

def _describe_match_types_payload() -> Dict[str, Any]:
    return {
        "match_types": {
            "exact": "1:1 mapping; the source code translates fully to the target.",
            "partial": "Source code maps to part of the target's scope, or vice versa.",
            "broad": "Source code is semantically related but coverage differs.",
        },
        "edge_kinds": {
            "standard_standard": "Both sides are official standards (NAICS, ISIC, NACE, etc.).",
            "standard_domain": "Source is an official standard; target is a curated WoT domain taxonomy.",
            "domain_standard": "Source is a curated WoT domain taxonomy; target is an official standard.",
            "domain_domain": "Both sides are curated WoT domain taxonomies.",
        },
    }


# Tools without a current REST endpoint or that need a multi-step client.
# Listed here so the dispatcher can return a clear "not yet supported in HTTP
# mode; run with DATABASE_URL instead" rather than a 404 from httpx.

_HTTP_NOT_YET_IMPLEMENTED = {
    "list_crosswalks_by_kind": (
        "needs a REST endpoint that lists edges filtered by edge_kind. "
        "Add GET /api/v1/equivalences?edge_kind=... and wire here."
    ),
    "get_country_scope": (
        "needs a REST endpoint that resolves country -> applicable systems. "
        "Add GET /api/v1/countries/{codes}/scope and wire here."
    ),
    "get_audit_report": (
        "audit/provenance is exposed at /api/v1/audit/provenance but the "
        "MCP tool returns a different shape; needs a small wrapper."
    ),
}


# ----- master dispatch table -------------------------------------------------

DISPATCH_TABLE: Dict[str, Callable[[Dict[str, Any]], Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]]] = {
    "list_classification_systems": _list_systems,
    "search_systems": _search_systems,
    "get_industry": _get_industry,
    "browse_children": _browse_children,
    "get_ancestors": _get_ancestors,
    "get_equivalences": _get_equivalences,
    "translate_code": _translate_code,
    "translate_across_all_systems": _translate_across_all_systems,
    "get_sector_overview": _get_sector_overview,
    "search_classifications": _search_classifications,
    "find_by_keyword_all_systems": _find_by_keyword_all_systems,
    "explore_industry_tree": _explore_industry_tree,
    "compare_sector": _compare_sector,
    "get_system_diff": _get_system_diff,
    "get_siblings": _get_siblings,
    "get_subtree_summary": _get_subtree_summary,
    "resolve_ambiguous_code": _resolve_ambiguous_code,
    "get_crosswalk_coverage": _get_crosswalk_coverage,
    "get_leaf_count": _get_leaf_count,
    "get_region_mapping": _get_region_mapping,
    "get_country_taxonomy_profile": _get_country_taxonomy_profile,
    "classify_business": _classify_business,
}


def supported_tools() -> Tuple[str, ...]:
    """Tool names the HTTP dispatcher can serve. Anything not in this list
    either has a static local payload (`describe_match_types`) or raises
    NotImplementedError until its REST endpoint lands."""
    return tuple(DISPATCH_TABLE.keys()) + ("describe_match_types",)


async def dispatch_http(
    client: httpx.AsyncClient,
    tool_name: str,
    args: Dict[str, Any],
) -> Any:
    """Run an MCP tool call as an HTTP request. Returns the parsed JSON body.

    Raises:
      - NotImplementedError when the tool has no HTTP-mode wiring yet.
      - httpx.HTTPStatusError when the API returns 4xx or 5xx.
    """
    if tool_name == "describe_match_types":
        return _describe_match_types_payload()

    if tool_name in _HTTP_NOT_YET_IMPLEMENTED:
        raise NotImplementedError(
            f"MCP tool '{tool_name}' is not yet wired in HTTP mode: "
            f"{_HTTP_NOT_YET_IMPLEMENTED[tool_name]} "
            "Run the MCP server in DB mode (set DATABASE_URL) until this lands."
        )

    if tool_name not in DISPATCH_TABLE:
        raise NotImplementedError(
            f"MCP tool '{tool_name}' has no HTTP-mode dispatcher registered. "
            "Either add a new entry in DISPATCH_TABLE or run the MCP server "
            "in DB mode (set DATABASE_URL)."
        )

    method, path, params, body = DISPATCH_TABLE[tool_name](args)
    response = await client.request(
        method,
        path,
        params={k: v for k, v in params.items() if v is not None},
        json=body,
    )
    response.raise_for_status()
    return response.json()
