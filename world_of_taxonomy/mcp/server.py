"""MCP stdio transport server.

Reads JSON-RPC messages from stdin, processes them, writes responses to stdout.
Compatible with Claude Desktop and other MCP clients.

No external MCP SDK dependency - implements the protocol directly.
Requires Python 3.9+.

Usage:
    python -m world_of_taxonomy mcp

Modes:
    The server picks one of two modes at startup, in this order:

    HTTP mode (preferred for end users):
        Set WOT_API_KEY=wot_... (get one at
        https://worldoftaxonomy.com/developers). The server creates a
        single httpx.AsyncClient pre-configured with the key and
        dispatches every tool call as a request against the WoT REST
        API at WOT_API_BASE_URL (default https://wot.aixcelerator.ai).
        End users do not need a database.

    DB mode (development / self-hosting):
        Set DATABASE_URL pointing at a Postgres instance with the WoT
        schema loaded. The server holds a connection from an asyncpg
        pool for the lifetime of the stdio session and runs each tool
        handler against it directly. The published PyPI package does
        NOT use this path; it is for development and self-hosters.

    Both unset: the server prints an actionable message on stderr
    pointing at /developers and exits with code 2 so Claude Desktop's
    "MCP server failed to start" error is informative.
"""

import asyncio
import json
import os
import sys
from typing import Optional

from world_of_taxonomy.db import get_pool, close_pool
from world_of_taxonomy.mcp.protocol import handle_jsonrpc_request


_MISSING_KEY_MESSAGE = (
    "World Of Taxonomy MCP server: no credentials.\n\n"
    "Set WOT_API_KEY (preferred for end users; get one at\n"
    "https://worldoftaxonomy.com/developers) or DATABASE_URL\n"
    "(local development with direct DB access).\n"
)


def _check_credentials() -> None:
    """Fail fast at startup with an actionable message.

    Reads stdin/stdout for JSON-RPC, so we cannot rely on the client
    surfacing a runtime error. Emit the message on stderr and exit
    non-zero so Claude Desktop's "MCP server failed to start" error
    actually carries information the user can act on.
    """
    has_api_key = bool(os.environ.get("WOT_API_KEY", "").strip())
    has_db_url = bool(os.environ.get("DATABASE_URL", "").strip())
    if not has_api_key and not has_db_url:
        sys.stderr.write(_MISSING_KEY_MESSAGE)
        sys.stderr.flush()
        raise SystemExit(2)


def _wot_api_key() -> Optional[str]:
    """Return the Bearer token for HTTP-mode requests, or None."""
    key = os.environ.get("WOT_API_KEY", "").strip()
    return key or None


def _wot_api_base_url() -> str:
    """Return the WoT REST API base URL for HTTP-mode requests."""
    return os.environ.get("WOT_API_BASE_URL", "https://wot.aixcelerator.ai").rstrip("/")


async def _stdio_loop(*, conn=None, http_client=None) -> None:
    """Read JSON-RPC from stdin, dispatch, write responses to stdout.

    Exactly one of `conn` / `http_client` must be set. The dispatch
    layer in protocol.handle_jsonrpc_request decides DB vs HTTP based
    on which arg is present.
    """
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(
        lambda: protocol, sys.stdin
    )

    while True:
        try:
            line = await reader.readline()
            if not line:
                break  # EOF

            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue

            request = json.loads(line_str)
            response = await handle_jsonrpc_request(
                request, conn=conn, http_client=http_client,
            )

            if response is not None:  # Notifications don't get responses
                response_json = json.dumps(response)
                sys.stdout.write(response_json + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                },
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            print(f"MCP server error: {e}", file=sys.stderr)


async def run_stdio_server_http() -> None:
    """HTTP mode: dispatch every tool call against the WoT REST API."""
    import httpx

    api_key = _wot_api_key()
    base_url = _wot_api_base_url()
    timeout = float(os.environ.get("WOT_API_TIMEOUT_SECONDS", "30"))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "worldoftaxonomy-mcp/0.1.0",
    }
    async with httpx.AsyncClient(
        base_url=base_url, headers=headers, timeout=timeout,
    ) as http_client:
        await _stdio_loop(http_client=http_client)


async def run_stdio_server_db() -> None:
    """DB mode: dispatch tool calls against the local Postgres pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await _stdio_loop(conn=conn)
    await close_pool()


async def run_stdio_server() -> None:
    """Pick the right mode based on env and dispatch."""
    if _wot_api_key():
        await run_stdio_server_http()
    else:
        await run_stdio_server_db()


def main():
    """Entry point for the MCP server."""
    _check_credentials()
    asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
