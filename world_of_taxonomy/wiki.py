"""Wiki loader - shared utilities for reading curated wiki content.

Wiki files live in the project-root ``wiki/`` directory. This module provides
helpers to load metadata, individual pages, and build concatenated outputs
for MCP context injection and llms-full.txt generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

WIKI_DIR = Path(__file__).parent.parent / "wiki"


def load_wiki_meta() -> List[dict]:
    """Parse ``wiki/_meta.json`` and return the page list sorted by order."""
    meta_path = WIKI_DIR / "_meta.json"
    data = json.loads(meta_path.read_text())
    return sorted(data, key=lambda e: e["order"])


def load_wiki_page(slug: str) -> Optional[str]:
    """Read a single wiki page by slug. Returns None if not found."""
    meta = load_wiki_meta()
    for entry in meta:
        if entry["slug"] == slug:
            fpath = WIKI_DIR / entry["file"]
            if fpath.exists():
                return fpath.read_text()
            return None
    return None


def load_all_wiki_pages() -> Dict[str, str]:
    """Return a dict mapping slug -> markdown content for all pages."""
    meta = load_wiki_meta()
    pages: Dict[str, str] = {}
    for entry in meta:
        fpath = WIKI_DIR / entry["file"]
        if fpath.exists():
            pages[entry["slug"]] = fpath.read_text()
    return pages


def build_wiki_context() -> str:
    """Build a condensed context string for MCP instructions.

    Concatenates key wiki pages (getting-started, crosswalk-map,
    industry-classification, systems-catalog) into a single string
    suitable for injection into the MCP initialize response.
    Targets ~10-15K tokens (~40-60K chars).
    """
    priority_slugs = [
        "getting-started",
        "systems-catalog",
        "crosswalk-map",
        "industry-classification",
        "categories-and-sectors",
        "domain-vs-standard",
    ]
    parts = []
    parts.append("# WorldOfTaxonomy - AI Agent Context\n")
    parts.append(
        "This knowledge graph connects 1,000+ classification systems "
        "with 1.2M+ nodes and 321K+ crosswalk edges.\n"
    )

    meta = load_wiki_meta()
    slug_to_entry = {e["slug"]: e for e in meta}

    for slug in priority_slugs:
        entry = slug_to_entry.get(slug)
        if not entry:
            continue
        content = load_wiki_page(slug)
        if content:
            parts.append(f"\n---\n\n{content}")

    # Add brief list of remaining pages
    remaining = [e for e in meta if e["slug"] not in priority_slugs]
    if remaining:
        parts.append("\n---\n\n## Additional Guides\n")
        for entry in remaining:
            parts.append(f"- **{entry['title']}**: {entry['description']}")

    return "\n".join(parts)


def build_llms_full_txt() -> str:
    """Concatenate all wiki pages in order for llms-full.txt."""
    from world_of_taxonomy.canary import canary_block

    meta = load_wiki_meta()
    parts = []
    parts.append("# WorldOfTaxonomy - Full Reference Guide\n")
    parts.append(
        "> Unified Global Classification Knowledge Graph\n"
        "> 1,000+ systems, 1.2M+ nodes, 321K+ crosswalk edges.\n"
        "> Open source (MIT). Data is informational only - use at your own risk.\n"
    )

    for entry in meta:
        content = load_wiki_page(entry["slug"])
        if content:
            parts.append(f"\n{'=' * 72}")
            parts.append(f"# {entry['title']}")
            parts.append(f"{'=' * 72}\n")
            parts.append(content)

    # Append canary tokens at the tail so any corpus that ingests this
    # file carries our provenance markers. See world_of_taxonomy/canary.py.
    parts.append(canary_block())

    return "\n".join(parts)
