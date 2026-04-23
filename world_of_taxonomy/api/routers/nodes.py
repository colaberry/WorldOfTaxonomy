"""Nodes router - /api/v1/systems/{system_id}/nodes endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from world_of_taxonomy.api.deps import get_conn, get_current_user
from world_of_taxonomy.api.schemas import (
    NodeResponse,
    EquivalenceResponse,
    GenerateTaxonomyRequest,
    GenerateTaxonomyResponse,
    AcceptTaxonomyRequest,
    GeneratedNode,
)
from world_of_taxonomy.exceptions import NodeNotFoundError
from world_of_taxonomy.llm_client import LLMNotConfiguredError
from world_of_taxonomy.query.browse import get_node, get_children, get_ancestors
from world_of_taxonomy.query.equivalence import get_equivalences
from world_of_taxonomy.query.generate import generate_children, persist_generated_children
from world_of_taxonomy.query.provenance import (
    get_system_provenance_map,
    node_response_kwargs,
)

router = APIRouter(prefix="/api/v1/systems/{system_id}/nodes", tags=["nodes"])


@router.get("/{code}", response_model=NodeResponse)
async def get_node_detail(system_id: str, code: str, conn=Depends(get_conn)):
    """Get a single classification node."""
    try:
        node = await get_node(conn, system_id, code)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Node '{code}' not found in '{system_id}'")
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id, {})
    return NodeResponse(**node_response_kwargs(node, prov))


@router.get("/{code}/children", response_model=List[NodeResponse])
async def get_node_children(system_id: str, code: str, conn=Depends(get_conn)):
    """Get direct children of a node."""
    children = await get_children(conn, system_id, code)
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id, {})
    return [NodeResponse(**node_response_kwargs(c, prov)) for c in children]


@router.get("/{code}/ancestors", response_model=List[NodeResponse])
async def get_node_ancestors(system_id: str, code: str, conn=Depends(get_conn)):
    """Get the path from root to this node."""
    ancestors_list = await get_ancestors(conn, system_id, code)
    prov_map = await get_system_provenance_map(conn, [system_id])
    prov = prov_map.get(system_id, {})
    return [NodeResponse(**node_response_kwargs(a, prov)) for a in ancestors_list]


@router.get("/{code}/equivalences", response_model=List[EquivalenceResponse])
async def get_node_equivalences(
    system_id: str,
    code: str,
    edge_kind: Optional[str] = Query(
        None,
        description=(
            "Filter by edge kind (comma-separated). One or more of: "
            "standard_standard, standard_domain, domain_standard, domain_domain."
        ),
    ),
    conn=Depends(get_conn),
):
    """Get cross-system equivalences for a node."""
    equivs = await get_equivalences(conn, system_id, code)
    responses = [EquivalenceResponse(**e.__dict__) for e in equivs]
    if edge_kind:
        wanted = {k.strip() for k in edge_kind.split(",") if k.strip()}
        responses = [r for r in responses if r.edge_kind in wanted]
    return responses


@router.post("/{code}/generate", response_model=GenerateTaxonomyResponse)
async def generate_taxonomy_for_node(
    system_id: str,
    code: str,
    body: GenerateTaxonomyRequest,
    conn=Depends(get_conn),
    current_user=Depends(get_current_user),
):
    """Generate AI-suggested sub-classifications for a node (preview only, no DB write)."""
    try:
        nodes = await generate_children(conn, system_id, code, count=body.count)
    except LLMNotConfiguredError:
        raise HTTPException(
            status_code=503,
            detail="AI generation unavailable: set OLLAMA_API_KEY (primary) or OPENROUTER_API_KEY (fallback)",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")
    return GenerateTaxonomyResponse(
        parent_system_id=system_id,
        parent_code=code,
        nodes=nodes,
    )


@router.post("/{code}/generate/accept", response_model=List[NodeResponse])
async def accept_generated_taxonomy(
    system_id: str,
    code: str,
    body: AcceptTaxonomyRequest,
    conn=Depends(get_conn),
    current_user=Depends(get_current_user),
):
    """Persist user-accepted AI-generated nodes to the database."""
    try:
        rows = await persist_generated_children(conn, system_id, code, body.nodes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist nodes: {exc}")
    return [NodeResponse(**r) for r in rows]
