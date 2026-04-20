"""Equivalences router - /api/v1/equivalences endpoints."""

from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Query

from world_of_taxonomy.api.deps import get_conn
from world_of_taxonomy.api.schemas import CrosswalkStatResponse, EdgeKindStatResponse
from world_of_taxonomy.query.equivalence import (
    get_crosswalk_stats,
    get_crosswalk_stats_by_edge_kind,
)

router = APIRouter(prefix="/api/v1/equivalences", tags=["equivalences"])


@router.get(
    "/stats",
    response_model=Union[List[CrosswalkStatResponse], List[EdgeKindStatResponse]],
)
async def crosswalk_stats(
    system_id: Optional[str] = Query(None, description="Filter to a specific system"),
    group_by: Optional[str] = Query(
        None,
        description=(
            "Grouping dimension. Omit (default) for system-pair stats. "
            "Pass 'edge_kind' for counts grouped by the four edge kinds "
            "(standard_standard, standard_domain, domain_standard, domain_domain)."
        ),
    ),
    conn=Depends(get_conn),
):
    """Get counts of equivalence edges per system pair or per edge kind."""
    if group_by == "edge_kind":
        rows = await get_crosswalk_stats_by_edge_kind(conn)
        return [EdgeKindStatResponse(**r) for r in rows]

    stats = await get_crosswalk_stats(conn)
    if system_id:
        stats = [s for s in stats if s["source_system"] == system_id or s["target_system"] == system_id]
    return [CrosswalkStatResponse(**s) for s in stats]
