#!/usr/bin/env python3
"""Build llms-full.txt and llms.txt from wiki/ content.

Reads wiki/_meta.json for ordering, concatenates all wiki markdown files
with section separators, and writes to frontend/public/.

Usage:
    python scripts/build_llms_txt.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from world_of_taxonomy.mcp.protocol import build_tools_list
from world_of_taxonomy.wiki import build_llms_full_txt, load_wiki_meta

PUBLIC_DIR = PROJECT_ROOT / "frontend" / "public"


def main():
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    # Build llms-full.txt
    full_txt = build_llms_full_txt()
    full_path = PUBLIC_DIR / "llms-full.txt"
    full_path.write_text(full_txt)
    print(f"Wrote {full_path} ({len(full_txt):,} chars)")

    # Build llms.txt (short summary with link to full version)
    meta = load_wiki_meta()
    lines = [
        "# World Of Taxonomy",
        "",
        "> Unified Global Classification Knowledge Graph",
        "> 1,000+ systems, 1.2M+ nodes, 321K+ crosswalk edges.",
        "> Open source (MIT). Data is informational only - use at your own risk.",
        "",
        "Full classification guides available at: https://worldoftaxonomy.com/guide/",
        "Full LLM reference: https://worldoftaxonomy.com/llms-full.txt",
        "",
        "## Guide Pages",
        "",
    ]
    for entry in meta:
        lines.append(f"- [{entry['title']}](https://worldoftaxonomy.com/guide/{entry['slug']})")
    lines.append("")
    lines.append("## API")
    lines.append("Base URL: https://worldoftaxonomy.com/api/v1")
    lines.append("")
    lines.append("## MCP Server")
    lines.append("Install: python -m world_of_taxonomy mcp")
    lines.append(f"Transport: stdio, {len(build_tools_list())} tools, wiki resources")
    lines.append("")

    short_txt = "\n".join(lines)
    short_path = PUBLIC_DIR / "llms.txt"
    short_path.write_text(short_txt)
    print(f"Wrote {short_path} ({len(short_txt):,} chars)")


if __name__ == "__main__":
    main()
