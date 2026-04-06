"""Equivalences router — /api/v1/equivalences endpoints."""

from typing import List

from fastapi import APIRouter, Depends

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.api.schemas import CrosswalkStatResponse
from world_of_taxanomy.query.equivalence import get_crosswalk_stats

router = APIRouter(prefix="/api/v1/equivalences", tags=["equivalences"])


@router.get("/stats", response_model=List[CrosswalkStatResponse])
async def crosswalk_stats(conn=Depends(get_conn)):
    """Get counts of equivalence edges per system pair."""
    stats = await get_crosswalk_stats(conn)
    return [CrosswalkStatResponse(**s) for s in stats]
