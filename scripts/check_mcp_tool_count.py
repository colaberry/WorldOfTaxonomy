#!/usr/bin/env python3
"""Guard against drift between `build_tools_list()` and hardcoded MCP tool
counts scattered across docs, wiki, skills, and frontend copy.

Fails if any unallowlisted occurrence of `<N> tools` or `<N> MCP tools`
disagrees with `len(build_tools_list())`.

Allowlisted: historical release/milestone claims (CHANGELOG.md, ROADMAP.md)
and this script itself. Everything else must either match the live count
or be reworded to drop the number entirely.

Intended to run in CI alongside `check_no_em_dash.sh`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from world_of_taxonomy.mcp.protocol import build_tools_list

ALLOWLIST = {
    "CHANGELOG.md",
    "ROADMAP.md",
    "scripts/check_mcp_tool_count.py",
}

SEARCH_ROOTS = [
    "world_of_taxonomy",
    "frontend/src",
    "frontend/public",
    "docs",
    "wiki",
    "skills",
    "scripts",
    "tests",
    "README.md",
    "HANDOVER.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
]

SKIP_DIRS = {"node_modules", ".next", "__pycache__", ".git", "dist", "build", ".venv"}

# Paths (as posix strings, relative to PROJECT_ROOT) to skip because they are
# build artifacts copied from canonical sources elsewhere in the repo.
# frontend/src/content/{wiki,blog,crosswalk,tree} are populated by the
# `prebuild`/`predev` scripts in frontend/package.json from repo-root
# `wiki/`, `blog/`, `crosswalk-data/`, `tree-data/` - the root copies are
# authoritative.
SKIP_PATH_PREFIXES = (
    "frontend/src/content/",
)

FILE_SUFFIXES = {".md", ".mdx", ".ts", ".tsx", ".js", ".jsx", ".py", ".txt", ".json", ".yml", ".yaml"}

PATTERN = re.compile(r"\b(\d+)\s+(MCP\s+)?tools?\b", re.IGNORECASE)


def iter_files():
    for root in SEARCH_ROOTS:
        path = PROJECT_ROOT / root
        if not path.exists():
            continue
        if path.is_file():
            yield path
            continue
        for p in path.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix not in FILE_SUFFIXES:
                continue
            yield p


def main() -> int:
    expected = len(build_tools_list())
    mismatches: list[tuple[str, int, str, int]] = []

    for path in iter_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        if any(rel.startswith(prefix) for prefix in SKIP_PATH_PREFIXES):
            continue
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            for match in PATTERN.finditer(line):
                n = int(match.group(1))
                if n != expected:
                    mismatches.append((rel, lineno, line.strip(), n))

    if mismatches:
        print(f"MCP tool count mismatch: build_tools_list() has {expected} tools, "
              f"but found {len(mismatches)} stale reference(s):\n")
        for rel, lineno, line, n in mismatches:
            print(f"  {rel}:{lineno}  claims {n} tools")
            print(f"    {line}")
        print("\nFix: update the number to "
              f"{expected}, or reword to remove the count.")
        print("If the reference is a historical release/milestone claim, "
              "add the file to ALLOWLIST in this script.")
        return 1

    print(f"MCP tool count OK ({expected} tools, all references consistent).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
