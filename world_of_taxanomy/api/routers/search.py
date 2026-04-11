"""Search router - /api/v1/search endpoint."""

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.api.schemas import NodeResponse, NodeWithContextResponse
from world_of_taxanomy.query.browse import get_ancestors, get_children
from world_of_taxanomy.query.search import search_nodes

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    system_id: Optional[str] = Query(None, alias="system_id", description="Filter by system ID"),
    system: Optional[str] = Query(None, description="Filter by system ID (alias)"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    grouped: bool = Query(False, description="Return results grouped by system"),
    context: bool = Query(False, description="Include ancestors and children for each match"),
    conn=Depends(get_conn),
):
    """Full-text search across all classification systems."""
    system_filter = system_id or system
    results = await search_nodes(conn, q, system_id=system_filter, limit=limit)

    if context:
        output = []
        for node in results:
            ancestors = await get_ancestors(conn, node.system_id, node.code)
            children = await get_children(conn, node.system_id, node.code)
            node_resp = NodeResponse(**node.__dict__)
            entry = NodeWithContextResponse(
                **node_resp.model_dump(),
                ancestors=[NodeResponse(**a.__dict__) for a in ancestors if a.code != node.code],
                children=[NodeResponse(**c.__dict__) for c in children],
            )
            output.append(entry)
        return output

    if grouped:
        groups: Dict[str, List[NodeResponse]] = {}
        for node in results:
            groups.setdefault(node.system_id, []).append(NodeResponse(**node.__dict__))
        return groups

    return [NodeResponse(**r.__dict__) for r in results]
