"""MCP stdio transport server.

Reads JSON-RPC messages from stdin, processes them, writes responses to stdout.
Compatible with Claude Desktop and other MCP clients.

No external MCP SDK dependency - implements the protocol directly.
Requires Python 3.9+.

Usage:
    python -m world_of_taxanomy mcp
"""

import asyncio
import json
import sys

from world_of_taxanomy.db import get_pool, close_pool
from world_of_taxanomy.mcp.protocol import handle_jsonrpc_request


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
    asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
