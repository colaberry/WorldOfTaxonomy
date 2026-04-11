"""MCP tool handler functions.

Each handler takes a database connection and a dict of arguments,
calls the appropriate query layer function, and returns a
JSON-serializable result.
"""

from typing import Any, Dict, List

from world_of_taxanomy.exceptions import NodeNotFoundError, SystemNotFoundError
from world_of_taxanomy.query.browse import (
    get_systems, get_system, get_roots, get_node, get_children, get_ancestors,
)
from world_of_taxanomy.query.search import search_nodes
from world_of_taxanomy.query.equivalence import (
    get_equivalences as _get_equivalences,
    translate_code as _translate_code,
)


def _node_to_dict(node) -> Dict[str, Any]:
    """Convert a ClassificationNode to a JSON-serializable dict."""
    return {
        "system_id": node.system_id,
        "code": node.code,
        "title": node.title,
        "description": node.description,
        "level": node.level,
        "parent_code": node.parent_code,
        "sector_code": node.sector_code,
        "is_leaf": node.is_leaf,
    }


def _system_to_dict(system) -> Dict[str, Any]:
    """Convert a ClassificationSystem to a JSON-serializable dict."""
    return {
        "id": system.id,
        "name": system.name,
        "full_name": system.full_name,
        "region": system.region,
        "version": system.version,
        "authority": system.authority,
        "url": system.url,
        "node_count": system.node_count,
    }


def _equiv_to_dict(equiv) -> Dict[str, Any]:
    """Convert an Equivalence to a JSON-serializable dict."""
    return {
        "source_system": equiv.source_system,
        "source_code": equiv.source_code,
        "target_system": equiv.target_system,
        "target_code": equiv.target_code,
        "match_type": equiv.match_type,
        "source_title": equiv.source_title,
        "target_title": equiv.target_title,
    }


# ── Tool handlers ────────────────────────────────────────────


async def handle_list_classification_systems(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """List all classification systems."""
    systems = await get_systems(conn)
    return [_system_to_dict(s) for s in systems]


async def handle_get_industry(
    conn, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Get details for a specific industry code."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    try:
        node = await get_node(conn, system_id, code)
        return _node_to_dict(node)
    except NodeNotFoundError:
        return {"error": f"Node '{code}' not found in '{system_id}'"}


async def handle_browse_children(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Get direct children of an industry code."""
    system_id = args.get("system_id", "")
    parent_code = args.get("parent_code", "")
    children = await get_children(conn, system_id, parent_code)
    return [_node_to_dict(c) for c in children]


async def handle_get_ancestors(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Get the path from root to a specific code."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    ancestors_list = await get_ancestors(conn, system_id, code)
    return [_node_to_dict(a) for a in ancestors_list]


async def handle_search_classifications(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Search across classification systems."""
    query = args.get("query", "")
    system_id = args.get("system_id")
    limit = args.get("limit", 20)
    results = await search_nodes(conn, query, system_id=system_id, limit=limit)
    return [_node_to_dict(r) for r in results]


async def handle_get_equivalences(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Get cross-system equivalences for a code."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    equivs = await _get_equivalences(conn, system_id, code)
    return [_equiv_to_dict(e) for e in equivs]


async def handle_translate_code(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Translate a code from one system to another."""
    source_system = args.get("source_system", "")
    source_code = args.get("source_code", "")
    target_system = args.get("target_system", "")
    results = await _translate_code(conn, source_system, source_code, target_system)
    return [_equiv_to_dict(r) for r in results]


async def handle_get_sector_overview(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Get top-level sectors/sections for a system."""
    system_id = args.get("system_id", "")
    roots = await get_roots(conn, system_id)
    return [_node_to_dict(r) for r in roots]


# ── Extended tool handlers ────────────────────────────────────


async def handle_translate_across_all_systems(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Translate a code to every other system in one call."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    equivs = await _get_equivalences(conn, system_id, code)
    return [_equiv_to_dict(e) for e in equivs]


async def handle_compare_sector(
    conn, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Return top-level sectors for two systems side by side."""
    system_id_a = args.get("system_id_a", "")
    system_id_b = args.get("system_id_b", "")
    roots_a = await get_roots(conn, system_id_a)
    roots_b = await get_roots(conn, system_id_b)
    return {
        "system_a": [_node_to_dict(n) for n in roots_a],
        "system_b": [_node_to_dict(n) for n in roots_b],
    }


async def handle_find_by_keyword_all_systems(
    conn, args: Dict[str, Any]
) -> Dict[str, List[Dict]]:
    """Search all systems and return results grouped by system ID."""
    query = args.get("query", "")
    limit_per_system = args.get("limit_per_system", 10)
    results = await search_nodes(conn, query, limit=200)
    grouped: Dict[str, List[Dict]] = {}
    for node in results:
        bucket = grouped.setdefault(node.system_id, [])
        if len(bucket) < limit_per_system:
            bucket.append(_node_to_dict(node))
    return grouped


async def handle_get_crosswalk_coverage(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Return per-system-pair equivalence edge counts."""
    from world_of_taxanomy.query.equivalence import get_crosswalk_stats
    stats = await get_crosswalk_stats(conn)
    system_id = args.get("system_id")
    if system_id:
        stats = [
            s for s in stats
            if s["source_system"] == system_id or s["target_system"] == system_id
        ]
    return stats


async def handle_get_system_diff(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Return nodes in system A that have no equivalence edge to system B."""
    system_id_a = args.get("system_id_a", "")
    system_id_b = args.get("system_id_b", "")
    rows = await conn.fetch(
        """SELECT n.*
           FROM classification_node n
           WHERE n.system_id = $1
             AND NOT EXISTS (
               SELECT 1 FROM equivalence e
               WHERE e.source_system = $1
                 AND e.source_code = n.code
                 AND e.target_system = $2
             )
           ORDER BY n.seq_order, n.code""",
        system_id_a, system_id_b,
    )
    from world_of_taxanomy.query.browse import _row_to_node
    return [_node_to_dict(_row_to_node(r)) for r in rows]


async def handle_get_siblings(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Return nodes that share the same parent as the given code."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    row = await conn.fetchrow(
        "SELECT parent_code FROM classification_node WHERE system_id = $1 AND code = $2",
        system_id, code,
    )
    if row is None or row["parent_code"] is None:
        return []
    siblings = await get_children(conn, system_id, row["parent_code"])
    return [_node_to_dict(s) for s in siblings if s.code != code]


async def handle_get_subtree_summary(
    conn, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Return aggregate stats for all nodes under a given code."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    try:
        root_node = await get_node(conn, system_id, code)
    except Exception:
        return {"error": f"Node '{code}' not found in '{system_id}'"}

    row = await conn.fetchrow(
        """WITH RECURSIVE subtree AS (
               SELECT code, level, is_leaf
               FROM classification_node
               WHERE system_id = $1 AND code = $2
             UNION ALL
               SELECT n.code, n.level, n.is_leaf
               FROM classification_node n
               JOIN subtree s ON n.parent_code = s.code AND n.system_id = $1
           )
           SELECT COUNT(*) AS total_nodes,
                  COUNT(CASE WHEN is_leaf THEN 1 END) AS leaf_count,
                  MAX(level) AS max_level
           FROM subtree""",
        system_id, code,
    )
    root_level = root_node.level
    return {
        "system_id": system_id,
        "code": code,
        "title": root_node.title,
        "total_nodes": row["total_nodes"],
        "leaf_count": row["leaf_count"],
        "max_depth": (row["max_level"] or root_level) - root_level,
    }


async def handle_resolve_ambiguous_code(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Find all systems that contain a given code."""
    code = args.get("code", "")
    rows = await conn.fetch(
        """SELECT * FROM classification_node
           WHERE code = $1
           ORDER BY system_id""",
        code,
    )
    from world_of_taxanomy.query.browse import _row_to_node
    return [_node_to_dict(_row_to_node(r)) for r in rows]


async def handle_get_leaf_count(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Return total and leaf node counts per system."""
    system_id = args.get("system_id")
    if system_id:
        rows = await conn.fetch(
            """SELECT system_id,
                      COUNT(*) AS total_nodes,
                      COUNT(CASE WHEN is_leaf THEN 1 END) AS leaf_nodes
               FROM classification_node
               WHERE system_id = $1
               GROUP BY system_id""",
            system_id,
        )
    else:
        rows = await conn.fetch(
            """SELECT system_id,
                      COUNT(*) AS total_nodes,
                      COUNT(CASE WHEN is_leaf THEN 1 END) AS leaf_nodes
               FROM classification_node
               GROUP BY system_id
               ORDER BY system_id"""
        )
    return [dict(r) for r in rows]


async def handle_get_region_mapping(
    conn, args: Dict[str, Any]
) -> Dict[str, List[Dict]]:
    """Return classification systems grouped by region."""
    systems = await get_systems(conn)
    grouped: Dict[str, List[Dict]] = {}
    for s in systems:
        grouped.setdefault(s.region, []).append(_system_to_dict(s))
    return grouped


async def handle_describe_match_types(
    conn, args: Dict[str, Any]
) -> Dict[str, str]:
    """Return definitions for each equivalence match type."""
    return {
        "exact": (
            "The two codes cover exactly the same economic activity. "
            "Every establishment in one code belongs in the other."
        ),
        "partial": (
            "The codes overlap substantially but not completely. "
            "One code may be broader or include additional activities not in the other."
        ),
        "broad": (
            "The codes are related but differ significantly in scope. "
            "Use as a rough guide only; manual review recommended for compliance purposes."
        ),
    }


async def handle_explore_industry_tree(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Search by keyword and return each match with its ancestor path and children."""
    query = args.get("query", "")
    system_id = args.get("system_id")
    limit = args.get("limit", 10)
    matches = await search_nodes(conn, query, system_id=system_id, limit=limit)
    results = []
    for node in matches:
        ancestors = await get_ancestors(conn, node.system_id, node.code)
        children = await get_children(conn, node.system_id, node.code)
        entry = _node_to_dict(node)
        # ancestors list includes the node itself - exclude it
        entry["ancestors"] = [_node_to_dict(a) for a in ancestors if a.code != node.code]
        entry["children"] = [_node_to_dict(c) for c in children]
        results.append(entry)
    return results
