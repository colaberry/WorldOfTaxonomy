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
from world_of_taxonomy.scope import resolve_country_scope

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    system_id: Optional[List[str]] = Query(
        None,
        alias="system_id",
        description=(
            "Filter by system ID. Pass multiple times to match any of several "
            "systems: ?system_id=naics_2022&system_id=isic_rev4."
        ),
    ),
    system: Optional[List[str]] = Query(
        None, description="Filter by system ID (alias, repeatable)."
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by category: 'domain' or 'standard'. Omit for both.",
    ),
    countries: Optional[List[str]] = Query(
        None,
        description=(
            "Optional ISO 3166-1 alpha-2 country codes. Scopes results to "
            "systems applicable to these countries plus universal recommended "
            "standards (UN/WCO/WHO). Pass multiple times to union: "
            "?countries=US&countries=CA."
        ),
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

    system_filter_list = system_id or system or []
    single_system = system_filter_list[0] if len(system_filter_list) == 1 else None
    multi_systems = system_filter_list if len(system_filter_list) > 1 else None

    scope = await resolve_country_scope(conn, countries)
    scoped_ids = (
        scope["candidate_systems"]
        if scope and not single_system and not multi_systems
        else None
    )
    effective_system_ids = multi_systems if multi_systems else scoped_ids
    results = await search_nodes(
        conn, q, system_id=single_system, limit=limit, system_ids=effective_system_ids,
    )
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
        payload: Any = output
    elif grouped:
        groups: Dict[str, List[NodeResponse]] = {}
        for node in results:
            prov = prov_map.get(node.system_id, {})
            groups.setdefault(node.system_id, []).append(NodeResponse(**node.__dict__, **prov))
        payload = groups
    else:
        payload = [
            NodeResponse(**r.__dict__, **prov_map.get(r.system_id, {})) for r in results
        ]

    if scope is not None:
        return {"scope": scope, "results": payload}
    return payload
