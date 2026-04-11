"""Equivalences router - /api/v1/equivalences endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.api.schemas import CrosswalkStatResponse
from world_of_taxanomy.query.equivalence import get_crosswalk_stats

router = APIRouter(prefix="/api/v1/equivalences", tags=["equivalences"])


@router.get("/stats", response_model=List[CrosswalkStatResponse])
async def crosswalk_stats(
    system_id: Optional[str] = Query(None, description="Filter to a specific system"),
    conn=Depends(get_conn),
):
    """Get counts of equivalence edges per system pair."""
    stats = await get_crosswalk_stats(conn)
    if system_id:
        stats = [s for s in stats if s["source_system"] == system_id or s["target_system"] == system_id]
    return [CrosswalkStatResponse(**s) for s in stats]
