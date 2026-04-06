"""Search router — /api/v1/search endpoint."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.api.schemas import NodeResponse
from world_of_taxanomy.query.search import search_nodes

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search", response_model=List[NodeResponse])
async def search(
    q: str = Query(..., description="Search query"),
    system: Optional[str] = Query(None, description="Filter by system ID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    conn=Depends(get_conn),
):
    """Full-text search across all classification systems."""
    results = await search_nodes(conn, q, system_id=system, limit=limit)
    return [NodeResponse(**r.__dict__) for r in results]
