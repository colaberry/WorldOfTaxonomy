"""MCP JSON-RPC protocol handling.

Implements the Model Context Protocol without external dependencies.
Handles initialize, tools/list, tools/call, resources/list, resources/read.
"""

import json
from typing import Any, Dict, List, Optional

from world_of_taxonomy.wiki import build_wiki_context, load_wiki_meta, load_wiki_page

from world_of_taxonomy.mcp.handlers import (
    handle_list_classification_systems,
    handle_get_industry,
    handle_browse_children,
    handle_get_ancestors,
    handle_search_classifications,
    handle_get_equivalences,
    handle_translate_code,
    handle_get_sector_overview,
    handle_translate_across_all_systems,
    handle_compare_sector,
    handle_find_by_keyword_all_systems,
    handle_get_crosswalk_coverage,
    handle_list_crosswalks_by_kind,
    handle_get_system_diff,
    handle_get_siblings,
    handle_get_subtree_summary,
    handle_resolve_ambiguous_code,
    handle_get_leaf_count,
    handle_get_region_mapping,
    handle_describe_match_types,
    handle_get_country_taxonomy_profile,
    handle_get_country_scope,
    handle_explore_industry_tree,
    handle_get_audit_report,
    handle_classify_business,
)


# ── Tool definitions ─────────────────────────────────────────


def build_tools_list() -> List[Dict[str, Any]]:
    """Return the list of available MCP tools with JSON schemas."""
    return [
        {
            "name": "list_classification_systems",
            "description": (
                "List all available classification systems. Each entry includes a 'category' "
                "field: 'domain' for curated WoT Domain taxonomies (system_id prefix 'domain_', "
                "plain-language on-ramps such as truck freight types, insurance risk types) and "
                "'standard' for official standards (NAICS, ISIC, NACE, SIC, SOC, HS, ICD, ISO, ...). "
                "Pass 'country_code' (ISO 3166-1 alpha-2, e.g. 'DE', 'US', 'IN') to restrict "
                "the list to systems applicable in that country, ordered by relevance "
                "(official national standard first, then regional, recommended, historical)."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "Optional ISO 3166-1 alpha-2 country code to filter systems by applicability.",
                    },
                },
            },
        },
        {
            "name": "get_industry",
            "description": "Get details for a specific industry code including title, level, and hierarchy position.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "Classification system ID (e.g., 'naics_2022', 'isic_rev4')",
                    },
                    "code": {
                        "type": "string",
                        "description": "Industry code (e.g., '6211', '8620')",
                    },
                },
                "required": ["system_id", "code"],
            },
        },
        {
            "name": "browse_children",
            "description": "Get direct children of an industry code to navigate the hierarchy.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "Classification system ID",
                    },
                    "parent_code": {
                        "type": "string",
                        "description": "Parent code to list children of",
                    },
                },
                "required": ["system_id", "parent_code"],
            },
        },
        {
            "name": "get_ancestors",
            "description": "Get the full path from root to a specific industry code.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "Classification system ID",
                    },
                    "code": {
                        "type": "string",
                        "description": "Industry code to trace ancestry for",
                    },
                },
                "required": ["system_id", "code"],
            },
        },
        {
            "name": "search_classifications",
            "description": (
                "Full-text search across classification systems. Searches titles and codes. "
                "Each result carries a 'category' field ('domain' vs 'standard') so callers "
                "can split results into curated WoT Domain taxonomies and official standards. "
                "Pass `countries` to scope candidates to that country's applicable systems "
                "plus universal recommended standards (UN/WCO/WHO); the result also includes "
                "a `scope` object showing the resolved country-specific vs global buckets."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'hospital', 'farming', '6211')",
                    },
                    "system_id": {
                        "type": "string",
                        "description": "Optional: filter results to a specific system",
                    },
                    "countries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional ISO 3166-1 alpha-2 country codes (e.g. ['US'], "
                            "['US','CA','MX']). Scopes candidates to applicable systems + "
                            "universal standards. Not a hard filter - global standards "
                            "recommended for any selected country stay in the pool."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default: 20)",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_equivalences",
            "description": "Get cross-system equivalences for an industry code (e.g., NAICS to ISIC mappings).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "Source classification system ID",
                    },
                    "code": {
                        "type": "string",
                        "description": "Source industry code",
                    },
                },
                "required": ["system_id", "code"],
            },
        },
        {
            "name": "translate_code",
            "description": "Translate an industry code from one system to another (e.g., NAICS 6211 → ISIC).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "source_system": {
                        "type": "string",
                        "description": "Source system ID (e.g., 'naics_2022')",
                    },
                    "source_code": {
                        "type": "string",
                        "description": "Source industry code",
                    },
                    "target_system": {
                        "type": "string",
                        "description": "Target system ID (e.g., 'isic_rev4')",
                    },
                },
                "required": ["source_system", "source_code", "target_system"],
            },
        },
        {
            "name": "get_sector_overview",
            "description": "Get top-level sectors/sections for a classification system.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "Classification system ID",
                    },
                },
                "required": ["system_id"],
            },
        },
        {
            "name": "translate_across_all_systems",
            "description": "Translate an industry code to every other system in one call. Returns all known equivalences.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "Source system ID (e.g., 'naics_2022')"},
                    "code": {"type": "string", "description": "Source industry code"},
                },
                "required": ["system_id", "code"],
            },
        },
        {
            "name": "compare_sector",
            "description": "Compare top-level sectors of two classification systems side by side.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id_a": {"type": "string", "description": "First system ID"},
                    "system_id_b": {"type": "string", "description": "Second system ID"},
                },
                "required": ["system_id_a", "system_id_b"],
            },
        },
        {
            "name": "find_by_keyword_all_systems",
            "description": "Search a keyword across all systems, returning results grouped by system.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"},
                    "limit_per_system": {"type": "integer", "description": "Max results per system (default: 10)"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_crosswalk_coverage",
            "description": "Show how many equivalence edges exist between each pair of classification systems. Every item includes an edge_kind (standard_standard, standard_domain, domain_standard, domain_domain).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "Optional: filter to a specific system"},
                },
            },
        },
        {
            "name": "list_crosswalks_by_kind",
            "description": (
                "List equivalence edges of a given edge_kind with counts and a sample. "
                "Useful for 'show me every standard-to-domain bridge' style queries."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "edge_kind": {
                        "type": "string",
                        "enum": [
                            "standard_standard",
                            "standard_domain",
                            "domain_standard",
                            "domain_domain",
                        ],
                        "description": "Which edge_kind to list.",
                    },
                    "system_id": {
                        "type": "string",
                        "description": "Optional: restrict to edges touching this system.",
                    },
                    "sample_limit": {
                        "type": "integer",
                        "description": "Max sample edges to include (default 10, max 100).",
                    },
                },
                "required": ["edge_kind"],
            },
        },
        {
            "name": "get_system_diff",
            "description": "Find codes in system A that have no equivalence mapping to system B.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id_a": {"type": "string", "description": "System to check codes from"},
                    "system_id_b": {"type": "string", "description": "System to check coverage against"},
                },
                "required": ["system_id_a", "system_id_b"],
            },
        },
        {
            "name": "get_siblings",
            "description": "Get other industry codes at the same level under the same parent.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "Classification system ID"},
                    "code": {"type": "string", "description": "Industry code to find siblings for"},
                },
                "required": ["system_id", "code"],
            },
        },
        {
            "name": "get_subtree_summary",
            "description": "Summarize all codes under a given node: total count, leaf count, max depth.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "Classification system ID"},
                    "code": {"type": "string", "description": "Root code of the subtree"},
                },
                "required": ["system_id", "code"],
            },
        },
        {
            "name": "resolve_ambiguous_code",
            "description": "Find all classification systems that contain a given code (e.g., '0111' exists in ISIC, SIC, and NIC).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Industry code to look up across all systems"},
                },
                "required": ["code"],
            },
        },
        {
            "name": "get_leaf_count",
            "description": "Compare granularity across systems: total nodes and leaf (most-specific) node counts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "Optional: filter to one system"},
                },
            },
        },
        {
            "name": "get_region_mapping",
            "description": "List classification systems grouped by geographic region.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "describe_match_types",
            "description": "Explain what exact, partial, and broad equivalence match types mean.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "explore_industry_tree",
            "description": "Search by keyword and return each matching node with its full ancestor path and immediate children - for navigating the classification hierarchy.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword to search (e.g., 'pharmaceutical', 'fintech')"},
                    "system_id": {"type": "string", "description": "Optional: restrict to one system"},
                    "limit": {"type": "integer", "description": "Max matches to return (default: 10)"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_audit_report",
            "description": (
                "Generate an aggregate audit report for data trustworthiness review. "
                "Returns: provenance tier breakdown (nodes per tier), official_download systems "
                "missing file hashes, structural derivation accounting (intentional copies), "
                "and skeleton systems (fewer than 30 nodes). Use this when an auditor needs "
                "to verify data provenance, trustworthiness, and completeness."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "get_country_taxonomy_profile",
            "description": (
                "Get the classification systems applicable to a country, plus its known sector strengths. "
                "Use this when a user says they are based in or operate in a specific country, or when "
                "a multinational wants to know which taxonomy to use in a given market. "
                "Returns: official national system (e.g. WZ 2008 for Germany, NIC 2008 for India), "
                "regional system (NACE Rev 2 for EU countries), the globally recommended ISIC Rev 4 "
                "standard, and the country's known sector strengths from the geo-sector crosswalk."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 country code (e.g. 'DE', 'PK', 'MX', 'ID', 'US', 'IN')",
                    },
                },
                "required": ["country_code"],
            },
        },
        {
            "name": "classify_business",
            "description": (
                "Classify a business, product, occupation, or activity description against "
                "global taxonomy systems. Results are split into two categories: "
                "'domain_matches' (curated WoT Domain taxonomies - plain-language on-ramps "
                "like truck freight types, insurance product types, AI deployment types) and "
                "'standard_matches' (official standards like NAICS, ISIC, NACE, SIC, SOC, HS, "
                "ICD, ISO). Each match carries a 'category' field. Example: 'organic baby "
                "food manufacturer' returns domain matches (food-service types) plus standard "
                "matches (NAICS 311422, ISIC 1030, HS 2007). "
                "Pass `countries` to scope candidates to that country's applicable systems "
                "plus universal recommended standards (UN/WCO/WHO). `countries` overrides "
                "`systems` when both are set. The response includes a `scope` object when "
                "countries are supplied, showing country-specific vs global candidates. "
                "Results are informational only; use at your own risk."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Free-text description of the business, product, service, occupation, or activity to classify",
                    },
                    "systems": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of system IDs to search (e.g., ['naics_2022', 'hs_2022']). Default: all major systems.",
                    },
                    "countries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional ISO 3166-1 alpha-2 country codes. Scopes candidates "
                            "to applicable systems + universal standards. Not a hard filter."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum matches per system (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["text"],
            },
        },
        {
            "name": "get_country_scope",
            "description": (
                "Introspection tool: given one or more ISO 3166-1 alpha-2 country codes, "
                "return the candidate classification systems that `search_classifications` "
                "and `classify_business` would use when scoped to those countries. Returns "
                "`country_specific_systems` (relevance=official/regional), "
                "`global_standard_systems` (relevance=recommended universal standards), and "
                "`candidate_systems` (the union). Use this before search/classify when the "
                "agent wants to reason about what's in scope before committing."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "countries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ISO 3166-1 alpha-2 country codes, e.g. ['US'] or ['US','CA','MX'].",
                    },
                },
                "required": ["countries"],
            },
        },
    ]


# ── Resource definitions ─────────────────────────────────────


def build_resources_list() -> List[Dict[str, Any]]:
    """Return the list of available MCP resources."""
    resources = [
        {
            "uri": "taxonomy://systems",
            "name": "Classification Systems",
            "description": "List of all industry classification systems in the knowledge graph.",
            "mimeType": "application/json",
        },
        {
            "uri": "taxonomy://stats",
            "name": "Knowledge Graph Statistics",
            "description": "Statistics about the classification systems and crosswalk edges.",
            "mimeType": "application/json",
        },
    ]
    # Add wiki page resources
    for entry in load_wiki_meta():
        resources.append({
            "uri": f"taxonomy://wiki/{entry['slug']}",
            "name": entry["title"],
            "description": entry["description"],
            "mimeType": "text/markdown",
        })
    return resources


# ── Tool dispatch ────────────────────────────────────────────

_TOOL_HANDLERS = {
    "list_classification_systems": handle_list_classification_systems,
    "get_industry": handle_get_industry,
    "browse_children": handle_browse_children,
    "get_ancestors": handle_get_ancestors,
    "search_classifications": handle_search_classifications,
    "get_equivalences": handle_get_equivalences,
    "translate_code": handle_translate_code,
    "get_sector_overview": handle_get_sector_overview,
    "translate_across_all_systems": handle_translate_across_all_systems,
    "compare_sector": handle_compare_sector,
    "find_by_keyword_all_systems": handle_find_by_keyword_all_systems,
    "get_crosswalk_coverage": handle_get_crosswalk_coverage,
    "list_crosswalks_by_kind": handle_list_crosswalks_by_kind,
    "get_system_diff": handle_get_system_diff,
    "get_siblings": handle_get_siblings,
    "get_subtree_summary": handle_get_subtree_summary,
    "resolve_ambiguous_code": handle_resolve_ambiguous_code,
    "get_leaf_count": handle_get_leaf_count,
    "get_region_mapping": handle_get_region_mapping,
    "describe_match_types": handle_describe_match_types,
    "get_country_taxonomy_profile": handle_get_country_taxonomy_profile,
    "get_country_scope": handle_get_country_scope,
    "explore_industry_tree": handle_explore_industry_tree,
    "get_audit_report": handle_get_audit_report,
    "classify_business": handle_classify_business,
}


# ── Resource handlers ────────────────────────────────────────


async def _handle_resource_read(conn, uri: str) -> Dict[str, Any]:
    """Handle a resources/read request."""
    if uri == "taxonomy://systems":
        from world_of_taxonomy.query.browse import get_systems
        systems = await get_systems(conn)
        data = [
            {
                "id": s.id, "name": s.name, "full_name": s.full_name,
                "region": s.region, "node_count": s.node_count,
                "source_url": s.source_url,
                "source_date": s.source_date,
                "data_provenance": s.data_provenance,
                "license": s.license,
                "source_file_hash": s.source_file_hash,
            }
            for s in systems
        ]
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(data, indent=2),
            }]
        }

    if uri == "taxonomy://stats":
        from world_of_taxonomy.query.equivalence import get_crosswalk_stats
        stats = await get_crosswalk_stats(conn)
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(stats, indent=2),
            }]
        }

    # Wiki page resources
    if uri.startswith("taxonomy://wiki/"):
        slug = uri[len("taxonomy://wiki/"):]
        content = load_wiki_page(slug)
        if content is None:
            return None
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "text/markdown",
                "text": content,
            }]
        }

    return None


# ── JSON-RPC request handler ─────────────────────────────────


async def handle_jsonrpc_request(
    request: Dict[str, Any],
    conn=None,
) -> Dict[str, Any]:
    """Handle a single JSON-RPC request and return a response.

    Args:
        request: Parsed JSON-RPC request dict.
        conn: asyncpg connection (required for data-fetching methods).

    Returns:
        JSON-RPC response dict.
    """
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    # ── initialize ──
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                },
                "serverInfo": {
                    "name": "WorldOfTaxonomy",
                    "version": "0.1.0",
                },
                "instructions": build_wiki_context(),
            },
        }

    # ── tools/list ──
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": build_tools_list()},
        }

    # ── tools/call ──
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = _TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}",
                },
            }

        try:
            result = await handler(conn, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, indent=2),
                    }],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }

    # ── resources/list ──
    if method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"resources": build_resources_list()},
        }

    # ── resources/read ──
    if method == "resources/read":
        uri = params.get("uri", "")
        result = await _handle_resource_read(conn, uri)
        if result is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": f"Unknown resource: {uri}",
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    # ── notifications (no response needed) ──
    if method == "notifications/initialized":
        return None  # No response for notifications

    # ── unknown method ──
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }
