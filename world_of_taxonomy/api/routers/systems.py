"""Systems router - /api/v1/systems endpoints."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from world_of_taxonomy.api.deps import get_conn
from world_of_taxonomy.api.schemas import SystemResponse, SystemDetailResponse, NodeResponse
from world_of_taxonomy.exceptions import SystemNotFoundError
from world_of_taxonomy.query.browse import get_systems, get_system, get_roots, get_systems_for_country
from world_of_taxonomy.query.provenance import get_system_provenance_map

router = APIRouter(prefix="/api/v1/systems", tags=["systems"])


def _system_matches_query(system, q_lower: str) -> bool:
    haystack = " ".join(
        (v or "")
        for v in (system.id, system.name, system.full_name, system.authority, system.region)
    ).lower()
    return q_lower in haystack


@router.get("")
async def list_systems(
    group_by: Optional[str] = Query(None, description="Group results (e.g. 'region')"),
    country: Optional[str] = Query(None, description="Filter by ISO 3166-1 alpha-2 country code (e.g. DE, PK, MX)"),
    category: Optional[str] = Query(
        None,
        description="Filter by category: 'domain' for curated Domain taxonomies, 'standard' for official standards (NAICS, ISIC, ...), omit for all.",
    ),
    q: Optional[str] = Query(
        None,
        description="Optional case-insensitive substring filter across id, name, full_name, authority, and region.",
    ),
    conn=Depends(get_conn),
):
    """List all classification systems, optionally filtered by country, category, name query, or grouped."""
    if country:
        rows = await get_systems_for_country(conn, country)
        if q:
            q_lower = q.strip().lower()
            rows = [r for r in rows if _system_matches_query(r, q_lower)]
        return rows

    if category is not None and category not in ("domain", "standard"):
        raise HTTPException(
            status_code=400,
            detail="category must be 'domain' or 'standard'",
        )

    systems = await get_systems(conn)
    if category:
        systems = [s for s in systems if s.category == category]
    if q:
        q_lower = q.strip().lower()
        systems = [s for s in systems if _system_matches_query(s, q_lower)]

    if group_by == "region":
        grouped: Dict[str, List[SystemResponse]] = {}
        for s in systems:
            grouped.setdefault(s.region or "Unknown", []).append(SystemResponse(**s.__dict__))
        return grouped
    return [SystemResponse(**s.__dict__) for s in systems]


@router.get("/{system_id}", response_model=SystemDetailResponse)
async def get_system_detail(system_id: str, conn=Depends(get_conn)):
    """Get a classification system with its root nodes."""
    try:
        system = await get_system(conn, system_id)
    except SystemNotFoundError:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found")

    roots = await get_roots(conn, system_id)
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id, {})
    root_responses = [NodeResponse(**r.__dict__, **prov) for r in roots]

    return SystemDetailResponse(**system.__dict__, roots=root_responses)
