#!/bin/bash
# MCP server launcher for Claude Desktop.
# Sets PYTHONPATH so world_of_taxonomy is importable regardless of cwd
# and sources DATABASE_URL from the gitignored .env file.
#
# Never hardcode DATABASE_URL or any other secret in this file.
# An earlier version of this file leaked a Neon connection string
# (commit 9cd3582, 2026-04-16). The leaked credential has been rotated;
# do not let this regress.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$REPO_ROOT"

# Load .env from the repo root (gitignored). Required for DATABASE_URL.
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$REPO_ROOT/.env"
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set. Add it to $REPO_ROOT/.env." >&2
  exit 1
fi

exec /usr/bin/python3 -m world_of_taxonomy mcp
