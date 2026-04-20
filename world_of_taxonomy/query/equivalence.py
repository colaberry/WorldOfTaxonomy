"""Cross-system equivalence queries."""

from typing import Dict, List, Optional

from world_of_taxonomy.models import Equivalence


def _row_to_equivalence(row) -> Equivalence:
    """Convert a database row to an Equivalence."""
    return Equivalence(
        source_system=row["source_system"],
        source_code=row["source_code"],
        target_system=row["target_system"],
        target_code=row["target_code"],
        match_type=row["match_type"],
        notes=row.get("notes"),
        source_title=row.get("source_title"),
        target_title=row.get("target_title"),
    )


async def get_equivalences(
    conn, system_id: str, code: str
) -> List[Equivalence]:
    """Get all equivalences for a node (outgoing edges)."""
    rows = await conn.fetch(
        """SELECT e.*,
                  s.title AS source_title,
                  t.title AS target_title
           FROM equivalence e
           LEFT JOIN classification_node s
             ON s.system_id = e.source_system AND s.code = e.source_code
           LEFT JOIN classification_node t
             ON t.system_id = e.target_system AND t.code = e.target_code
           WHERE e.source_system = $1 AND e.source_code = $2
           ORDER BY e.target_system, e.target_code""",
        system_id, code,
    )
    return [_row_to_equivalence(r) for r in rows]


async def translate_code(
    conn,
    source_system: str,
    source_code: str,
    target_system: str,
) -> List[Equivalence]:
    """Translate a code from one system to another."""
    rows = await conn.fetch(
        """SELECT e.*,
                  s.title AS source_title,
                  t.title AS target_title
           FROM equivalence e
           LEFT JOIN classification_node s
             ON s.system_id = e.source_system AND s.code = e.source_code
           LEFT JOIN classification_node t
             ON t.system_id = e.target_system AND t.code = e.target_code
           WHERE e.source_system = $1
             AND e.source_code = $2
             AND e.target_system = $3
           ORDER BY e.match_type, e.target_code""",
        source_system, source_code, target_system,
    )
    return [_row_to_equivalence(r) for r in rows]


async def get_crosswalk_sections(
    conn,
    source_system: str,
    target_system: str,
) -> Dict:
    """Get a section-level summary of crosswalk edges grouped by root ancestor.

    Returns top-level groupings so the UI can show a navigable overview
    instead of rendering hundreds of flat nodes at once.
    """
    # 1. Get all edges between the two systems
    edges = await conn.fetch(
        """SELECT source_system, source_code, target_system, target_code, match_type
           FROM equivalence
           WHERE (source_system = $1 AND target_system = $2)
              OR (source_system = $2 AND target_system = $1)""",
        source_system, target_system,
    )

    if not edges:
        return {
            "source_system": source_system,
            "target_system": target_system,
            "sections": [],
            "total_edges": 0,
        }

    # 2. Build parent/title lookup for both systems
    parent_map: Dict[tuple, Optional[str]] = {}
    title_map: Dict[tuple, str] = {}
    for sys_id in {source_system, target_system}:
        rows = await conn.fetch(
            "SELECT code, parent_code, title FROM classification_node WHERE system_id = $1",
            sys_id,
        )
        for r in rows:
            parent_map[(sys_id, r["code"])] = r["parent_code"]
            title_map[(sys_id, r["code"])] = r["title"]

    # 3. Walk up to root ancestor for each code (with caching)
    root_cache: Dict[tuple, str] = {}

    def find_root(sys: str, code: str) -> str:
        key = (sys, code)
        if key in root_cache:
            return root_cache[key]
        chain: List[str] = []
        cur = code
        visited: set = set()
        while cur and (sys, cur) in parent_map:
            chain.append(cur)
            parent = parent_map[(sys, cur)]
            if parent is None or parent in visited:
                break
            visited.add(cur)
            cur = parent
        root = cur if cur else code
        for c in chain:
            root_cache[(sys, c)] = root
        return root

    # 4. Group edges by (source_root, target_root)
    groups: Dict[tuple, Dict] = {}
    for e in edges:
        src_sys = e["source_system"]
        tgt_sys = e["target_system"]
        src_root = find_root(src_sys, e["source_code"])
        tgt_root = find_root(tgt_sys, e["target_code"])

        # Normalize direction: source_system param is always "source"
        if src_sys == source_system:
            key = (src_root, tgt_root)
        else:
            key = (tgt_root, src_root)

        if key not in groups:
            s_code, t_code = key
            groups[key] = {
                "source_section": s_code,
                "source_title": title_map.get((source_system, s_code), s_code),
                "target_section": t_code,
                "target_title": title_map.get((target_system, t_code), t_code),
                "edge_count": 0,
                "exact_count": 0,
            }
        groups[key]["edge_count"] += 1
        if e["match_type"] == "exact":
            groups[key]["exact_count"] += 1

    sections = sorted(groups.values(), key=lambda s: -s["edge_count"])

    return {
        "source_system": source_system,
        "target_system": target_system,
        "sections": sections,
        "total_edges": len(edges),
    }


async def get_crosswalk_graph(
    conn,
    source_system: str,
    target_system: str,
    limit: int = 500,
    section: Optional[str] = None,
) -> Dict:
    """Get a graph of crosswalk edges between two systems.

    Returns deduplicated edges (only source->target direction) with
    node metadata for building a Cytoscape.js visualization.

    When *section* is provided, only edges whose source or target code
    is a descendant of that section code are returned.
    """
    params: list = [source_system, target_system]
    section_filter = ""

    if section:
        # Build descendant sets for the section in both systems
        desc_rows = await conn.fetch(
            """WITH RECURSIVE desc AS (
                   SELECT system_id, code FROM classification_node
                   WHERE system_id IN ($1, $2) AND (code = $3 OR parent_code = $3)
                   UNION ALL
                   SELECT n.system_id, n.code FROM classification_node n
                   JOIN desc d ON n.parent_code = d.code AND n.system_id = d.system_id
               )
               SELECT system_id, code FROM desc""",
            source_system, target_system, section,
        )
        src_codes = [r["code"] for r in desc_rows if r["system_id"] == source_system]
        tgt_codes = [r["code"] for r in desc_rows if r["system_id"] == target_system]
        if not src_codes and not tgt_codes:
            return {
                "source_system": source_system,
                "target_system": target_system,
                "nodes": [],
                "edges": [],
                "total_edges": 0,
                "truncated": False,
            }
        params.extend([src_codes, tgt_codes])
        section_filter = """
           AND (
               (e.source_system = $1 AND e.source_code = ANY($3::text[]))
               OR (e.source_system = $2 AND e.source_code = ANY($4::text[]))
               OR (e.target_system = $1 AND e.target_code = ANY($3::text[]))
               OR (e.target_system = $2 AND e.target_code = ANY($4::text[]))
           )"""

    # Get deduplicated edges (use LEAST/GREATEST to pick canonical direction)
    all_rows = await conn.fetch(
        f"""SELECT DISTINCT ON (
                LEAST(source_system, target_system),
                LEAST(source_code, target_code),
                GREATEST(source_code, target_code)
           )
           e.source_system, e.source_code, e.target_system, e.target_code,
           e.match_type,
           s.title AS source_title,
           t.title AS target_title
           FROM equivalence e
           LEFT JOIN classification_node s
             ON s.system_id = e.source_system AND s.code = e.source_code
           LEFT JOIN classification_node t
             ON t.system_id = e.target_system AND t.code = e.target_code
           WHERE ((e.source_system = $1 AND e.target_system = $2)
              OR (e.source_system = $2 AND e.target_system = $1))
              {section_filter}
           ORDER BY
             LEAST(source_system, target_system),
             LEAST(source_code, target_code),
             GREATEST(source_code, target_code),
             e.id
        """,
        *params,
    )

    total_edges = len(all_rows)
    truncated = total_edges > limit
    rows = all_rows[:limit]

    # Build unique nodes from edges
    node_map: Dict[str, Dict] = {}
    edges = []
    for r in rows:
        src_id = f"{r['source_system']}:{r['source_code']}"
        tgt_id = f"{r['target_system']}:{r['target_code']}"
        if src_id not in node_map:
            node_map[src_id] = {
                "id": src_id,
                "system": r["source_system"],
                "code": r["source_code"],
                "title": r["source_title"] or r["source_code"],
            }
        if tgt_id not in node_map:
            node_map[tgt_id] = {
                "id": tgt_id,
                "system": r["target_system"],
                "code": r["target_code"],
                "title": r["target_title"] or r["target_code"],
            }
        edges.append({
            "source": src_id,
            "target": tgt_id,
            "match_type": r["match_type"],
        })

    return {
        "source_system": source_system,
        "target_system": target_system,
        "nodes": list(node_map.values()),
        "edges": edges,
        "total_edges": total_edges,
        "truncated": truncated,
    }


async def get_crosswalk_stats(conn) -> List[Dict]:
    """Get counts of equivalence edges per system pair."""
    rows = await conn.fetch(
        """SELECT source_system, target_system,
                  COUNT(*) AS edge_count,
                  COUNT(CASE WHEN match_type = 'exact' THEN 1 END) AS exact_count,
                  COUNT(CASE WHEN match_type = 'partial' THEN 1 END) AS partial_count
           FROM equivalence
           GROUP BY source_system, target_system
           ORDER BY source_system, target_system"""
    )
    return [dict(r) for r in rows]


async def get_crosswalk_stats_by_edge_kind(conn) -> List[Dict]:
    """Get counts of equivalence edges grouped by computed edge_kind.

    edge_kind is derived from whether each endpoint's system_id starts
    with 'domain_' (domain taxonomy) vs anything else (official standard).
    """
    rows = await conn.fetch(
        """SELECT
                CASE WHEN starts_with(source_system, 'domain_') THEN 'domain' ELSE 'standard' END
                || '_' ||
                CASE WHEN starts_with(target_system, 'domain_') THEN 'domain' ELSE 'standard' END
                AS edge_kind,
                COUNT(*) AS edge_count,
                COUNT(CASE WHEN match_type = 'exact'   THEN 1 END) AS exact_count,
                COUNT(CASE WHEN match_type = 'partial' THEN 1 END) AS partial_count,
                COUNT(CASE WHEN match_type = 'broad'   THEN 1 END) AS broad_count
           FROM equivalence
           GROUP BY edge_kind
           ORDER BY edge_count DESC"""
    )
    return [dict(r) for r in rows]
