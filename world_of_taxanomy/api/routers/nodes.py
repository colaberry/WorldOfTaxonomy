"""Nodes router - /api/v1/systems/{system_id}/nodes endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.api.schemas import NodeResponse, EquivalenceResponse
from world_of_taxanomy.exceptions import NodeNotFoundError
from world_of_taxanomy.query.browse import get_node, get_children, get_ancestors
from world_of_taxanomy.query.equivalence import get_equivalences

router = APIRouter(prefix="/api/v1/systems/{system_id}/nodes", tags=["nodes"])


@router.get("/{code}", response_model=NodeResponse)
async def get_node_detail(system_id: str, code: str, conn=Depends(get_conn)):
    """Get a single classification node."""
    try:
        node = await get_node(conn, system_id, code)
    except NodeNotFoundError:
        raise HTTPException(status_code=404, detail=f"Node '{code}' not found in '{system_id}'")
    return NodeResponse(**node.__dict__)


@router.get("/{code}/children", response_model=List[NodeResponse])
async def get_node_children(system_id: str, code: str, conn=Depends(get_conn)):
    """Get direct children of a node."""
    children = await get_children(conn, system_id, code)
    return [NodeResponse(**c.__dict__) for c in children]


@router.get("/{code}/ancestors", response_model=List[NodeResponse])
async def get_node_ancestors(system_id: str, code: str, conn=Depends(get_conn)):
    """Get the path from root to this node."""
    ancestors_list = await get_ancestors(conn, system_id, code)
    return [NodeResponse(**a.__dict__) for a in ancestors_list]


@router.get("/{code}/equivalences", response_model=List[EquivalenceResponse])
async def get_node_equivalences(system_id: str, code: str, conn=Depends(get_conn)):
    """Get cross-system equivalences for a node."""
    equivs = await get_equivalences(conn, system_id, code)
    return [EquivalenceResponse(**e.__dict__) for e in equivs]
