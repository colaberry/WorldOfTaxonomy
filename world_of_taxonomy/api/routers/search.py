"""Search router - /api/v1/search endpoint."""

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from world_of_taxonomy.api.deps import get_conn
from world_of_taxonomy.api.schemas import NodeResponse, NodeWithContextResponse
from world_of_taxonomy.category import get_category
from world_of_taxonomy.query.browse import get_ancestors, get_children
from world_of_taxonomy.query.search import search_nodes
from world_of_taxonomy.query.provenance import get_system_provenance_map

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    system_id: Optional[str] = Query(None, alias="system_id", description="Filter by system ID"),
    system: Optional[str] = Query(None, description="Filter by system ID (alias)"),
    category: Optional[str] = Query(
        None,
        description="Filter by category: 'domain' or 'standard'. Omit for both.",
    ),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    grouped: bool = Query(False, description="Return results grouped by system"),
    context: bool = Query(False, description="Include ancestors and children for each match"),
    conn=Depends(get_conn),
):
    """Full-text search across all classification systems."""
    if category is not None and category not in ("domain", "standard"):
        raise HTTPException(
            status_code=400,
            detail="category must be 'domain' or 'standard'",
        )

    system_filter = system_id or system
    results = await search_nodes(conn, q, system_id=system_filter, limit=limit)
    if category:
        results = [r for r in results if get_category(r.system_id) == category]

    # Fetch provenance for all systems in the result set (single query)
    sys_ids = list({r.system_id for r in results})
    prov_map = await get_system_provenance_map(conn, sys_ids)

    if context:
        output = []
        for node in results:
            ancestors = await get_ancestors(conn, node.system_id, node.code)
            children = await get_children(conn, node.system_id, node.code)
            prov = prov_map.get(node.system_id, {})
            node_resp = NodeResponse(**node.__dict__, **prov)
            entry = NodeWithContextResponse(
                **node_resp.model_dump(),
                ancestors=[NodeResponse(**a.__dict__, **prov) for a in ancestors if a.code != node.code],
                children=[NodeResponse(**c.__dict__, **prov) for c in children],
            )
            output.append(entry)
        return output

    if grouped:
        groups: Dict[str, List[NodeResponse]] = {}
        for node in results:
            prov = prov_map.get(node.system_id, {})
            groups.setdefault(node.system_id, []).append(NodeResponse(**node.__dict__, **prov))
        return groups

    return [NodeResponse(**r.__dict__, **prov_map.get(r.system_id, {})) for r in results]
