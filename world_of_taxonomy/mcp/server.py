"""MCP stdio transport server.

Reads JSON-RPC messages from stdin, processes them, writes responses to stdout.
Compatible with Claude Desktop and other MCP clients.

No external MCP SDK dependency - implements the protocol directly.
Requires Python 3.9+.

Usage:
    python -m world_of_taxonomy mcp

Auth (Phase 6):
    The published `worldoftaxonomy-mcp` PyPI package will run in HTTP
    mode and require a `WOT_API_KEY` env var; missing-key startups
    print an actionable error and exit. The in-tree direct-DB mode
    (used by the WoT repo for development and tests) is gated on
    `DATABASE_URL` and never reaches the API. Production deployments
    install the PyPI package and set `WOT_API_KEY` from the user's
    /developers/keys dashboard.
"""

import asyncio
import json
import os
import sys
from typing import Optional

from world_of_taxonomy.db import get_pool, close_pool
from world_of_taxonomy.mcp.protocol import handle_jsonrpc_request


_MISSING_KEY_MESSAGE = (
    "WorldOfTaxonomy MCP server: no credentials.\n\n"
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
    """Return the Bearer token for HTTP-mode requests, or None.

    Hot path callers will use this when the future HTTP transport is
    wired in; PR #3 keeps the direct-DB code path so the in-tree
    development workflow does not regress.
    """
    key = os.environ.get("WOT_API_KEY", "").strip()
    return key or None


async def run_stdio_server():
    """Run the MCP server over stdin/stdout."""
    pool = await get_pool()

    # Read from stdin line by line (JSON-RPC messages are newline-delimited)
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(
        lambda: protocol, sys.stdin
    )

    async with pool.acquire() as conn:
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break  # EOF

                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                request = json.loads(line_str)
                response = await handle_jsonrpc_request(request, conn=conn)

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
                # Log to stderr (stdout is for JSON-RPC)
                print(f"MCP server error: {e}", file=sys.stderr)

    await close_pool()


def main():
    """Entry point for the MCP server."""
    _check_credentials()
    asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
