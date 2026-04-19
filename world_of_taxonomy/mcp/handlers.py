"""MCP tool handler functions.

Each handler takes a database connection and a dict of arguments,
calls the appropriate query layer function, and returns a
JSON-serializable result.
"""

from typing import Any, Dict, List

from world_of_taxonomy.category import get_category
from world_of_taxonomy.exceptions import NodeNotFoundError, SystemNotFoundError
from world_of_taxonomy.query.browse import (
    get_systems, get_system, get_roots, get_node, get_children, get_ancestors,
    get_systems_for_country, get_country_sector_strengths,
)
from world_of_taxonomy.query.search import search_nodes
from world_of_taxonomy.query.equivalence import (
    get_equivalences as _get_equivalences,
    translate_code as _translate_code,
)
from world_of_taxonomy.query.provenance import (
    get_system_provenance_map,
    enrich_node_dict,
    get_audit_report,
)


def _node_to_dict(node, prov: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert a ClassificationNode to a JSON-serializable dict.

    If prov is provided, attaches system-level provenance fields.
    """
    d = {
        "system_id": node.system_id,
        "code": node.code,
        "title": node.title,
        "description": node.description,
        "level": node.level,
        "parent_code": node.parent_code,
        "sector_code": node.sector_code,
        "is_leaf": node.is_leaf,
        "category": get_category(node.system_id),
    }
    if prov:
        enrich_node_dict(d, prov)
    return d


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
        "source_url": system.source_url,
        "source_date": system.source_date,
        "data_provenance": system.data_provenance,
        "license": system.license,
        "source_file_hash": system.source_file_hash,
        "category": get_category(system.id),
    }


def _equiv_to_dict(equiv) -> Dict[str, Any]:
    """Convert an Equivalence to a JSON-serializable dict."""
    from world_of_taxonomy.category import compute_edge_kind
    return {
        "source_system": equiv.source_system,
        "source_code": equiv.source_code,
        "target_system": equiv.target_system,
        "target_code": equiv.target_code,
        "match_type": equiv.match_type,
        "source_title": equiv.source_title,
        "target_title": equiv.target_title,
        "source_category": get_category(equiv.source_system),
        "target_category": get_category(equiv.target_system),
        "edge_kind": compute_edge_kind(equiv.source_system, equiv.target_system),
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
        prov_map = await get_system_provenance_map(conn, [system_id])
        return _node_to_dict(node, prov_map.get(system_id))
    except NodeNotFoundError:
        return {"error": f"Node '{code}' not found in '{system_id}'"}


async def handle_browse_children(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Get direct children of an industry code."""
    system_id = args.get("system_id", "")
    parent_code = args.get("parent_code", "")
    children = await get_children(conn, system_id, parent_code)
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id)
    return [_node_to_dict(c, prov) for c in children]


async def handle_get_ancestors(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Get the path from root to a specific code."""
    system_id = args.get("system_id", "")
    code = args.get("code", "")
    ancestors_list = await get_ancestors(conn, system_id, code)
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id)
    return [_node_to_dict(a, prov) for a in ancestors_list]


async def handle_search_classifications(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Search across classification systems."""
    query = args.get("query", "")
    system_id = args.get("system_id")
    limit = args.get("limit", 20)
    results = await search_nodes(conn, query, system_id=system_id, limit=limit)
    sys_ids = list({r.system_id for r in results})
    prov_map = await get_system_provenance_map(conn, sys_ids)
    return [_node_to_dict(r, prov_map.get(r.system_id)) for r in results]


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
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id)
    return [_node_to_dict(r, prov) for r in roots]


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
    prov_map = await get_system_provenance_map(conn, [system_id_a, system_id_b])
    return {
        "system_a": [_node_to_dict(n, prov_map.get(system_id_a)) for n in roots_a],
        "system_b": [_node_to_dict(n, prov_map.get(system_id_b)) for n in roots_b],
    }


async def handle_find_by_keyword_all_systems(
    conn, args: Dict[str, Any]
) -> Dict[str, List[Dict]]:
    """Search all systems and return results grouped by system ID."""
    query = args.get("query", "")
    limit_per_system = args.get("limit_per_system", 10)
    results = await search_nodes(conn, query, limit=200)
    sys_ids = list({r.system_id for r in results})
    prov_map = await get_system_provenance_map(conn, sys_ids)
    grouped: Dict[str, List[Dict]] = {}
    for node in results:
        bucket = grouped.setdefault(node.system_id, [])
        if len(bucket) < limit_per_system:
            bucket.append(_node_to_dict(node, prov_map.get(node.system_id)))
    return grouped


async def handle_get_crosswalk_coverage(
    conn, args: Dict[str, Any]
) -> List[Dict]:
    """Return per-system-pair equivalence edge counts."""
    from world_of_taxonomy.category import compute_edge_kind
    from world_of_taxonomy.query.equivalence import get_crosswalk_stats
    stats = await get_crosswalk_stats(conn)
    system_id = args.get("system_id")
    if system_id:
        stats = [
            s for s in stats
            if s["source_system"] == system_id or s["target_system"] == system_id
        ]
    return [
        {**s, "edge_kind": compute_edge_kind(s["source_system"], s["target_system"])}
        for s in stats
    ]


async def handle_list_crosswalks_by_kind(
    conn, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Return counts + sample edges for a given edge_kind.

    Lets agents answer "show me every standard-to-domain bridge touching
    NAICS" in one call. Optional system_id narrows both counts and samples
    to edges that touch the given system.
    """
    from world_of_taxonomy.category import compute_edge_kind
    from world_of_taxonomy.query.equivalence import get_crosswalk_stats_by_edge_kind

    edge_kind = args.get("edge_kind")
    if edge_kind not in {
        "standard_standard", "standard_domain",
        "domain_standard", "domain_domain",
    }:
        return {
            "error": (
                "edge_kind must be one of: standard_standard, standard_domain, "
                "domain_standard, domain_domain."
            ),
        }
    system_id = args.get("system_id")
    sample_limit = max(1, min(int(args.get("sample_limit", 10)), 100))

    totals = await get_crosswalk_stats_by_edge_kind(conn)
    total_for_kind = next(
        (row["edge_count"] for row in totals if row["edge_kind"] == edge_kind),
        0,
    )

    src_cat, tgt_cat = edge_kind.split("_")
    src_pred = "starts_with(e.source_system, 'domain_')"
    if src_cat == "standard":
        src_pred = f"NOT {src_pred}"
    tgt_pred = "starts_with(e.target_system, 'domain_')"
    if tgt_cat == "standard":
        tgt_pred = f"NOT {tgt_pred}"

    where_sql = f"WHERE {src_pred} AND {tgt_pred}"
    params: list = []
    if system_id:
        where_sql += " AND (e.source_system = $1 OR e.target_system = $1)"
        params.append(system_id)

    samples = await conn.fetch(
        f"""SELECT e.source_system, e.source_code, e.target_system, e.target_code,
                   e.match_type, e.notes,
                   s.title AS source_title,
                   t.title AS target_title
            FROM equivalence e
            LEFT JOIN classification_node s
              ON s.system_id = e.source_system AND s.code = e.source_code
            LEFT JOIN classification_node t
              ON t.system_id = e.target_system AND t.code = e.target_code
            {where_sql}
            ORDER BY e.source_system, e.source_code
            LIMIT {sample_limit}""",
        *params,
    )

    return {
        "edge_kind": edge_kind,
        "total_edges": total_for_kind,
        "system_id": system_id,
        "samples": [
            {
                "source_system": r["source_system"],
                "source_code": r["source_code"],
                "source_title": r["source_title"],
                "target_system": r["target_system"],
                "target_code": r["target_code"],
                "target_title": r["target_title"],
                "match_type": r["match_type"],
                "notes": r["notes"],
                "edge_kind": compute_edge_kind(r["source_system"], r["target_system"]),
            }
            for r in samples
        ],
    }


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
    from world_of_taxonomy.query.browse import _row_to_node
    prov_map = await get_system_provenance_map(conn, [system_id_a])
    prov = prov_map.get(system_id_a)
    return [_node_to_dict(_row_to_node(r), prov) for r in rows]


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
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id)
    return [_node_to_dict(s, prov) for s in siblings if s.code != code]


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
    from world_of_taxonomy.query.browse import _row_to_node
    sys_ids = list({r["system_id"] for r in rows})
    prov_map = await get_system_provenance_map(conn, sys_ids)
    return [_node_to_dict(_row_to_node(r), prov_map.get(r["system_id"])) for r in rows]


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
    sys_ids = list({m.system_id for m in matches})
    prov_map = await get_system_provenance_map(conn, sys_ids)
    results = []
    for node in matches:
        ancestors = await get_ancestors(conn, node.system_id, node.code)
        children = await get_children(conn, node.system_id, node.code)
        prov = prov_map.get(node.system_id)
        entry = _node_to_dict(node, prov)
        entry["ancestors"] = [_node_to_dict(a, prov) for a in ancestors if a.code != node.code]
        entry["children"] = [_node_to_dict(c, prov) for c in children]
        results.append(entry)
    return results


async def handle_get_audit_report(
    conn, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Return aggregate audit report for data trustworthiness review."""
    report = await get_audit_report(conn)
    # Convert system rows to dicts for JSON serialization
    from world_of_taxonomy.query.browse import _row_to_system
    report["official_missing_hash"] = [
        _system_to_dict(_row_to_system(r)) for r in report["official_missing_hash"]
    ]
    report["skeleton_systems"] = [
        _system_to_dict(_row_to_system(r)) for r in report["skeleton_systems"]
    ]
    return report


async def handle_get_country_taxonomy_profile(
    conn, args: Dict[str, Any]
) -> Dict:
    """Return taxonomy profile for a country: applicable systems + sector strengths."""
    country_code = args.get("country_code", "").upper()
    if not country_code or len(country_code) != 2:
        return {"error": "country_code must be a 2-letter ISO 3166-1 alpha-2 code (e.g. 'DE', 'PK', 'MX')"}

    # Country metadata
    country_row = await conn.fetchrow(
        """SELECT code, title, parent_code
           FROM classification_node
           WHERE system_id = 'iso_3166_1' AND code = $1""",
        country_code,
    )

    systems = await get_systems_for_country(conn, country_code)
    sector_strengths = await get_country_sector_strengths(conn, country_code)

    return {
        "country": {
            "code": country_code,
            "title": country_row["title"] if country_row else None,
            "parent_region": country_row["parent_code"] if country_row else None,
        },
        "classification_systems": systems,
        "sector_strengths": sector_strengths,
        "usage_tip": (
            f"For a company in {country_code}: use the 'official' system for local regulatory filings, "
            "'regional' for cross-border reporting within the region, and "
            "'recommended' (ISIC Rev 4) for international/UN comparisons."
        ),
    }


def _partition_classify_matches(matches: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split classify_text's flat match list by category (domain vs standard)."""
    domain: List[Dict[str, Any]] = []
    standard: List[Dict[str, Any]] = []
    for m in matches:
        stamped = dict(m)
        stamped["category"] = get_category(m["system_id"])
        if stamped["category"] == "domain":
            domain.append(stamped)
        else:
            standard.append(stamped)
    return domain, standard


async def handle_classify_business(
    conn, args: Dict[str, Any],
) -> Dict[str, Any]:
    """Classify free-text against taxonomy systems.

    Returns results split into:
      - domain_matches: curated WoT domain taxonomies (plain-language on-ramps)
      - standard_matches: official standards (NAICS, ISIC, NACE, SIC, SOC, ...)
    The legacy flat "matches" key is intentionally absent.
    """
    from world_of_taxonomy.classify import classify_text

    text = args.get("text", "")
    if not text or len(text) < 2:
        return {"error": "text must be at least 2 characters"}

    systems = args.get("systems")
    limit = args.get("limit", 5)

    result = await classify_text(
        conn,
        text=text,
        system_ids=systems,
        limit=limit,
    )

    if result.get("compound"):
        atoms_out = []
        for atom in result.get("atoms", []):
            d, s = _partition_classify_matches(atom.get("matches", []))
            atoms_out.append({
                "phrase": atom["phrase"],
                "domain_matches": d,
                "standard_matches": s,
            })
        hero = result.get("hero")
        hero_domain, hero_standard = _partition_classify_matches(
            hero.get("matches", []) if hero else []
        )
        return {
            "query": result["query"],
            "compound": True,
            "atoms": atoms_out,
            "hero": {
                "phrase": hero["phrase"] if hero else None,
                "domain_matches": hero_domain,
                "standard_matches": hero_standard,
            } if hero else None,
            "domain_matches": hero_domain,
            "standard_matches": hero_standard,
            "crosswalks": result.get("crosswalks", []),
            "cta": result.get("cta"),
            "disclaimer": result["disclaimer"],
            "report_issue_url": result["report_issue_url"],
        }

    domain, standard = _partition_classify_matches(result.get("matches", []))
    return {
        "query": result["query"],
        "compound": False,
        "domain_matches": domain,
        "standard_matches": standard,
        "crosswalks": result.get("crosswalks", []),
        "disclaimer": result["disclaimer"],
        "report_issue_url": result["report_issue_url"],
        "llm_used": result.get("llm_used", False),
        "llm_keywords": result.get("llm_keywords", []),
    }
