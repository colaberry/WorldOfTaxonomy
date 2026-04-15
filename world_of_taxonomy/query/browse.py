"""Hierarchy navigation queries.

Functions for browsing classification trees: get nodes, children,
ancestors, subtrees, and system metadata.
"""

from typing import List

from world_of_taxonomy.exceptions import NodeNotFoundError, SystemNotFoundError
from world_of_taxonomy.models import ClassificationNode, ClassificationSystem


def _row_to_system(row) -> ClassificationSystem:
    """Convert a database row to a ClassificationSystem."""
    source_date = row.get("source_date")
    if source_date is not None:
        source_date = str(source_date)
    return ClassificationSystem(
        id=row["id"],
        name=row["name"],
        full_name=row["full_name"],
        region=row["region"],
        version=row["version"],
        authority=row["authority"],
        url=row["url"],
        tint_color=row["tint_color"],
        node_count=row["node_count"],
        source_url=row.get("source_url"),
        source_date=source_date,
        data_provenance=row.get("data_provenance"),
        license=row.get("license"),
        source_file_hash=row.get("source_file_hash"),
    )


def _row_to_node(row) -> ClassificationNode:
    """Convert a database row to a ClassificationNode."""
    return ClassificationNode(
        id=row["id"],
        system_id=row["system_id"],
        code=row["code"],
        title=row["title"],
        description=row.get("description"),
        level=row["level"],
        parent_code=row.get("parent_code"),
        sector_code=row.get("sector_code"),
        is_leaf=row["is_leaf"],
        seq_order=row.get("seq_order", 0),
    )


async def get_systems(conn) -> List[ClassificationSystem]:
    """List all classification systems."""
    rows = await conn.fetch(
        "SELECT * FROM classification_system ORDER BY name"
    )
    return [_row_to_system(r) for r in rows]


async def get_system(conn, system_id: str) -> ClassificationSystem:
    """Get a single classification system by ID."""
    row = await conn.fetchrow(
        "SELECT * FROM classification_system WHERE id = $1",
        system_id,
    )
    if row is None:
        raise SystemNotFoundError(system_id)
    return _row_to_system(row)


async def get_roots(conn, system_id: str) -> List[ClassificationNode]:
    """Get top-level nodes (sectors/sections) for a system."""
    # Find the minimum level in the system (NAICS=1, ISIC=0)
    min_level = await conn.fetchval(
        "SELECT MIN(level) FROM classification_node WHERE system_id = $1",
        system_id,
    )
    if min_level is None:
        return []

    rows = await conn.fetch(
        """SELECT * FROM classification_node
           WHERE system_id = $1 AND level = $2
           ORDER BY seq_order, code""",
        system_id, min_level,
    )
    return [_row_to_node(r) for r in rows]


async def get_node(conn, system_id: str, code: str) -> ClassificationNode:
    """Get a single node by system and code."""
    row = await conn.fetchrow(
        "SELECT * FROM classification_node WHERE system_id = $1 AND code = $2",
        system_id, code,
    )
    if row is None:
        raise NodeNotFoundError(system_id, code)
    return _row_to_node(row)


async def get_children(
    conn, system_id: str, parent_code: str
) -> List[ClassificationNode]:
    """Get direct children of a node."""
    rows = await conn.fetch(
        """SELECT * FROM classification_node
           WHERE system_id = $1 AND parent_code = $2
           ORDER BY seq_order, code""",
        system_id, parent_code,
    )
    return [_row_to_node(r) for r in rows]


async def get_ancestors(
    conn, system_id: str, code: str
) -> List[ClassificationNode]:
    """Get the path from root to this node (inclusive).

    Returns list ordered from root to the target node.
    """
    # Walk up the tree by following parent_code
    path = []
    current_code = code

    while current_code is not None:
        row = await conn.fetchrow(
            "SELECT * FROM classification_node WHERE system_id = $1 AND code = $2",
            system_id, current_code,
        )
        if row is None:
            break
        path.append(_row_to_node(row))
        current_code = row["parent_code"]

    # Reverse so root is first
    path.reverse()
    return path


async def get_systems_for_country(conn, country_code: str) -> list:
    """Return classification systems applicable to a country.

    Queries country_system_link joined with classification_system.
    Returns list ordered by relevance (official first, then regional,
    recommended, historical).
    """
    rows = await conn.fetch(
        """SELECT cs.id, cs.name, cs.full_name, cs.region, cs.version,
                  cs.authority, cs.url, cs.tint_color, cs.node_count,
                  csl.relevance, csl.notes AS csl_notes
           FROM country_system_link csl
           JOIN classification_system cs ON cs.id = csl.system_id
           WHERE csl.country_code = $1
           ORDER BY
             CASE csl.relevance
               WHEN 'official'     THEN 1
               WHEN 'regional'     THEN 2
               WHEN 'recommended'  THEN 3
               WHEN 'historical'   THEN 4
               ELSE 5
             END,
             cs.name""",
        country_code.upper(),
    )
    return [dict(r) for r in rows]


async def get_country_sector_strengths(conn, country_code: str) -> list:
    """Return sector strengths for a country from the geo-sector crosswalk.

    Queries the equivalence table for iso_3166_1 -> naics_2022 edges,
    joining with classification_node to get the NAICS sector title.
    """
    rows = await conn.fetch(
        """SELECT e.target_code AS naics_sector,
                  COALESCE(n.title, '') AS sector_name,
                  e.match_type,
                  e.notes
           FROM equivalence e
           LEFT JOIN classification_node n
             ON n.system_id = 'naics_2022' AND n.code = e.target_code
           WHERE e.source_system = 'iso_3166_1'
             AND e.source_code = $1
             AND e.target_system = 'naics_2022'
           ORDER BY e.match_type, e.target_code""",
        country_code.upper(),
    )
    return [dict(r) for r in rows]
