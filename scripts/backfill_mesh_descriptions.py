"""Backfill MeSH node descriptions from the NLM descriptor XML.

The structural ingester persists only the descriptor UI and its
preferred name. This script surfaces the definition (ScopeNote),
hierarchy placement (TreeNumberList), and entry terms (synonyms)
from the preferred concept into ``classification_node.description``
as structured markdown.

Usage:
    python -m scripts.backfill_mesh_descriptions              # prod
    python -m scripts.backfill_mesh_descriptions --dry-run    # no UPDATE
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.mesh_descriptions import (
    parse_mesh_descriptor_xml,
)


_SYSTEM_ID = "mesh"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_source(root: Path) -> Path:
    data = root / "data"
    # Prefer uncompressed xml, then .xml.gz
    xmls = sorted(data.glob("desc*.xml"))
    if xmls:
        return xmls[-1]
    gzs = sorted(data.glob("desc*.xml.gz"))
    if gzs:
        return gzs[-1]
    raise FileNotFoundError(
        "MeSH descriptor XML not found. Download from "
        "https://www.nlm.nih.gov/databases/download/mesh.html "
        "and place descYYYY.xml (or .xml.gz) under data/"
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _find_source(root)
    print(f"  Parsing {source.name} (may take ~30s; ~300 MB)...")
    mapping = parse_mesh_descriptor_xml(source)
    print(f"  Parsed {len(mapping):,} description rows")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null:,} MeSH nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update:,} rows")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        print(f"  Updated {updated:,} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null:,} MeSH nodes still have empty description")
    finally:
        await conn.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing to the database",
    )
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
