"""HTTP-transport bridge for the WorldOfTaxonomy MCP server.

Wraps the existing stdio-based JSON-RPC handler (``world_of_taxonomy.mcp.protocol``)
with a single FastAPI POST endpoint so MCP clients that speak Streamable HTTP
(including Claude Desktop's new remote-MCP support) can talk to the server
without a local Python install.

Transport model: a client sends one JSON-RPC message per POST and gets one
JSON-RPC response back. Server-initiated messages (notifications, progress,
sampling) are not emitted on this transport; all 25 tools are request/response
so this is sufficient for Claude Desktop's tools/* traffic today. If that
changes, upgrade to SSE or Streamable-HTTP chunked output here.

Use from Claude Desktop config::

    {
      "mcpServers": {
        "world-of-taxonomy": {
          "url": "https://wot.aixcelerator.ai/mcp"
        }
      }
    }
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from world_of_taxonomy.db import get_pool
from world_of_taxonomy.mcp.protocol import handle_jsonrpc_request

router = APIRouter(tags=["mcp"])


@router.post("/mcp")
async def mcp_http_bridge(request: Request) -> Response:
    """Handle one MCP JSON-RPC message over HTTP POST."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
        )

    pool = await get_pool()
    async with pool.acquire() as conn:
        response = await handle_jsonrpc_request(body, conn=conn)

    # Notifications ("method" w/o "id") return None — MCP spec says 202 No Body.
    if response is None:
        return Response(status_code=202)

    return JSONResponse(content=response)


@router.get("/mcp")
async def mcp_http_info() -> dict:
    """Friendly probe response so browsers/GET probes don't 405."""
    return {
        "transport": "streamable-http",
        "spec": "MCP 2025-03-26",
        "hint": "POST JSON-RPC messages to this URL",
        "tools_hint": "initialize first, then tools/list",
    }
