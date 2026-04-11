"""MCP JSON-RPC protocol handling.

Implements the Model Context Protocol without external dependencies.
Handles initialize, tools/list, tools/call, resources/list, resources/read.
"""

import json
from typing import Any, Dict, List, Optional

from world_of_taxanomy.mcp.handlers import (
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
    handle_get_system_diff,
    handle_get_siblings,
    handle_get_subtree_summary,
    handle_resolve_ambiguous_code,
    handle_get_leaf_count,
    handle_get_region_mapping,
    handle_describe_match_types,
    handle_explore_industry_tree,
)


# ── Tool definitions ─────────────────────────────────────────


def build_tools_list() -> List[Dict[str, Any]]:
    """Return the list of available MCP tools with JSON schemas."""
    return [
        {
            "name": "list_classification_systems",
            "description": "List all available industry classification systems (NAICS, ISIC, etc.)",
            "inputSchema": {
                "type": "object",
                "properties": {},
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
            "description": "Full-text search across industry classification systems. Searches titles and codes.",
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
            "description": "Show how many equivalence edges exist between each pair of classification systems.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "system_id": {"type": "string", "description": "Optional: filter to a specific system"},
                },
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
    ]


# ── Resource definitions ─────────────────────────────────────


def build_resources_list() -> List[Dict[str, Any]]:
    """Return the list of available MCP resources."""
    return [
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
    "get_system_diff": handle_get_system_diff,
    "get_siblings": handle_get_siblings,
    "get_subtree_summary": handle_get_subtree_summary,
    "resolve_ambiguous_code": handle_resolve_ambiguous_code,
    "get_leaf_count": handle_get_leaf_count,
    "get_region_mapping": handle_get_region_mapping,
    "describe_match_types": handle_describe_match_types,
    "explore_industry_tree": handle_explore_industry_tree,
}


# ── Resource handlers ────────────────────────────────────────


async def _handle_resource_read(conn, uri: str) -> Dict[str, Any]:
    """Handle a resources/read request."""
    if uri == "taxonomy://systems":
        from world_of_taxanomy.query.browse import get_systems
        systems = await get_systems(conn)
        data = [
            {
                "id": s.id, "name": s.name, "full_name": s.full_name,
                "region": s.region, "node_count": s.node_count,
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
        from world_of_taxanomy.query.equivalence import get_crosswalk_stats
        stats = await get_crosswalk_stats(conn)
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(stats, indent=2),
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
                    "name": "WorldOfTaxanomy",
                    "version": "0.1.0",
                },
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
