"""Hierarchy navigation queries.

Functions for browsing classification trees: get nodes, children,
ancestors, subtrees, and system metadata.
"""

from typing import List

from world_of_taxanomy.exceptions import NodeNotFoundError, SystemNotFoundError
from world_of_taxanomy.models import ClassificationNode, ClassificationSystem


def _row_to_system(row) -> ClassificationSystem:
    """Convert a database row to a ClassificationSystem."""
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
