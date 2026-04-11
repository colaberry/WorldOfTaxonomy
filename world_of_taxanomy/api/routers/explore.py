"""Explore router - cross-system and analytical endpoints.

GET /api/v1/systems/{id}/nodes/{code}/translations
GET /api/v1/systems/{id}/nodes/{code}/siblings
GET /api/v1/systems/{id}/nodes/{code}/subtree
GET /api/v1/compare?a=&b=
GET /api/v1/diff?a=&b=
GET /api/v1/nodes/{code}
GET /api/v1/systems/stats
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.api.schemas import (
    CompareSectorsResponse,
    EquivalenceResponse,
    NodeResponse,
    NodeWithContextResponse,
    SubtreeSummaryResponse,
    SystemGranularityResponse,
)
from world_of_taxanomy.exceptions import NodeNotFoundError, SystemNotFoundError
from world_of_taxanomy.query.browse import (
    get_ancestors,
    get_children,
    get_node,
    get_roots,
    get_system,
    get_systems,
)
from world_of_taxanomy.query.equivalence import get_equivalences

router = APIRouter()


# ── /systems/{id}/nodes/{code}/translations ───────────────────

@router.get(
    "/api/v1/systems/{system_id}/nodes/{code}/translations",
    response_model=List[EquivalenceResponse],
)
async def get_translations(
    system_id: str,
    code: str,
    conn=Depends(get_conn),
):
    """All cross-system mappings for a code in one call."""
    try:
        await get_node(conn, system_id, code)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Node '{code}' not found in '{system_id}'")
    equivs = await get_equivalences(conn, system_id, code)
    return equivs


# ── /systems/{id}/nodes/{code}/siblings ───────────────────────

@router.get(
    "/api/v1/systems/{system_id}/nodes/{code}/siblings",
    response_model=List[NodeResponse],
)
async def get_siblings(
    system_id: str,
    code: str,
    conn=Depends(get_conn),
):
    """Other nodes at the same level under the same parent."""
    try:
        node = await get_node(conn, system_id, code)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Node '{code}' not found in '{system_id}'")
    if node.parent_code is None:
        return []
    siblings = await get_children(conn, system_id, node.parent_code)
    return [s for s in siblings if s.code != code]


# ── /systems/{id}/nodes/{code}/subtree ────────────────────────

@router.get(
    "/api/v1/systems/{system_id}/nodes/{code}/subtree",
    response_model=SubtreeSummaryResponse,
)
async def get_subtree(
    system_id: str,
    code: str,
    conn=Depends(get_conn),
):
    """Aggregate stats for all nodes under a given code."""
    try:
        root_node = await get_node(conn, system_id, code)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Node '{code}' not found in '{system_id}'")
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
    return SubtreeSummaryResponse(
        system_id=system_id,
        code=code,
        title=root_node.title,
        total_nodes=row["total_nodes"],
        leaf_count=row["leaf_count"],
        max_depth=(row["max_level"] or root_node.level) - root_node.level,
    )


# ── /compare?a=&b= ────────────────────────────────────────────

@router.get(
    "/api/v1/compare",
    response_model=CompareSectorsResponse,
)
async def compare_systems(
    a: str = Query(..., description="First system ID"),
    b: str = Query(..., description="Second system ID"),
    conn=Depends(get_conn),
):
    """Side-by-side top-level sectors for two systems."""
    try:
        await get_system(conn, a)
    except SystemNotFoundError:
        raise HTTPException(status_code=404, detail=f"System '{a}' not found")
    try:
        await get_system(conn, b)
    except SystemNotFoundError:
        raise HTTPException(status_code=404, detail=f"System '{b}' not found")
    roots_a = await get_roots(conn, a)
    roots_b = await get_roots(conn, b)
    return CompareSectorsResponse(
        system_a=[NodeResponse(**r.__dict__) for r in roots_a],
        system_b=[NodeResponse(**r.__dict__) for r in roots_b],
    )


# ── /diff?a=&b= ───────────────────────────────────────────────

@router.get(
    "/api/v1/diff",
    response_model=List[NodeResponse],
)
async def get_system_diff(
    a: str = Query(..., description="Source system ID"),
    b: str = Query(..., description="Target system to check coverage against"),
    conn=Depends(get_conn),
):
    """Nodes in system A with no equivalence mapping to system B."""
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
        a, b,
    )
    from world_of_taxanomy.query.browse import _row_to_node
    return [_row_to_node(r) for r in rows]


# ── /nodes/{code} ─────────────────────────────────────────────

@router.get(
    "/api/v1/nodes/{code}",
    response_model=List[NodeResponse],
)
async def resolve_code(
    code: str,
    conn=Depends(get_conn),
):
    """Find all systems that contain a given code."""
    rows = await conn.fetch(
        "SELECT * FROM classification_node WHERE code = $1 ORDER BY system_id",
        code,
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Code '{code}' not found in any system")
    from world_of_taxanomy.query.browse import _row_to_node
    return [_row_to_node(r) for r in rows]


# ── /systems/stats ────────────────────────────────────────────

@router.get(
    "/api/v1/systems/stats",
    response_model=List[SystemGranularityResponse],
)
async def get_systems_stats(
    system_id: Optional[str] = None,
    conn=Depends(get_conn),
):
    """Per-system leaf and total node counts."""
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
