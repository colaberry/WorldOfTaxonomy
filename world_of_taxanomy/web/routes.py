"""Web frontend routes — serves Jinja2 templates."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.exceptions import NodeNotFoundError, SystemNotFoundError
from world_of_taxanomy.models import SECTOR_COLORS
from world_of_taxanomy.query.browse import (
    get_systems, get_system, get_roots, get_node, get_children, get_ancestors,
)
from world_of_taxanomy.query.equivalence import get_equivalences

# Templates directory
_web_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(_web_dir / "templates"))

router = APIRouter(tags=["web"])

# Sector color lookup for templates
_sector_color_map = {
    "11": "#4ADE80", "21": "#F59E0B", "22": "#06B6D4", "23": "#EF4444",
    "31-33": "#8B5CF6", "42": "#EC4899", "44-45": "#F97316", "48-49": "#14B8A6",
    "51": "#3B82F6", "52": "#6366F1", "53": "#A78BFA", "54": "#10B981",
    "55": "#64748B", "56": "#78716C", "61": "#2563EB", "62": "#0D9488",
    "71": "#E11D48", "72": "#D97706", "81": "#9CA3AF", "92": "#1E40AF",
    # ISIC/NACE/ANZSIC/SIC/JSIC sections (letter-based)
    "A": "#4ADE80", "B": "#F59E0B", "C": "#8B5CF6", "D": "#06B6D4",
    "E": "#14B8A6", "F": "#EF4444", "G": "#F97316", "H": "#14B8A6",
    "I": "#D97706", "J": "#3B82F6", "K": "#6366F1", "L": "#A78BFA",
    "M": "#10B981", "N": "#78716C", "O": "#1E40AF", "P": "#2563EB",
    "Q": "#0D9488", "R": "#E11D48", "S": "#9CA3AF", "T": "#64748B",
    "U": "#7A7872",
    # SIC 1987 divisions (overlap with letters above is fine)
}


async def _nav_systems(conn):
    """Fetch all classification systems for nav dropdown."""
    try:
        return await get_systems(conn)
    except Exception:
        return []


@router.get("/", response_class=HTMLResponse)
async def galaxy_view(request: Request, conn=Depends(get_conn)):
    """Galaxy View — landing page with d3-force constellation."""
    systems = await _nav_systems(conn)
    return templates.TemplateResponse(request, "index.html", {
        "active_nav": "galaxy",
        "nav_systems": systems,
    })


@router.get("/explore", response_class=HTMLResponse)
async def explore_view(request: Request, conn=Depends(get_conn)):
    """Bubble Explorer — recursive force-directed drill-down."""
    systems = await _nav_systems(conn)
    return templates.TemplateResponse(request, "explore.html", {
        "active_nav": "explore",
        "nav_systems": systems,
    })


@router.get("/system/{system_id}", response_class=HTMLResponse)
async def system_view(request: Request, system_id: str, conn=Depends(get_conn)):
    """System View — sector treemap + sector cards."""
    try:
        system = await get_system(conn, system_id)
    except SystemNotFoundError:
        return HTMLResponse(status_code=404, content="System not found")

    roots = await get_roots(conn, system_id)

    systems = await _nav_systems(conn)
    return templates.TemplateResponse(request, "system.html", {
        "system": system,
        "roots": roots,
        "sector_colors": _sector_color_map,
        "active_nav": system_id.split("_")[0],
        "nav_systems": systems,
    })


@router.get("/system/{system_id}/{code}", response_class=HTMLResponse)
async def node_view(request: Request, system_id: str, code: str, conn=Depends(get_conn)):
    """Node View — detail page with tree sidebar, children, equivalences, MCP block."""
    try:
        system = await get_system(conn, system_id)
        node = await get_node(conn, system_id, code)
    except (SystemNotFoundError, NodeNotFoundError):
        return HTMLResponse(status_code=404, content="Node not found")

    ancestors_list = await get_ancestors(conn, system_id, code)
    children_list = await get_children(conn, system_id, code)
    equivalences_list = await get_equivalences(conn, system_id, code)

    systems = await _nav_systems(conn)
    return templates.TemplateResponse(request, "node.html", {
        "system": system,
        "node": node,
        "ancestors": ancestors_list,
        "children": children_list,
        "equivalences": equivalences_list,
        "active_nav": system_id.split("_")[0],
        "nav_systems": systems,
    })
