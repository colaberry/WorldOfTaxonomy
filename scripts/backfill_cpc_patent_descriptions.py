"""Backfill CPC Patent node descriptions from the Full-Definition XML archive.

The structural ingester at :mod:`world_of_taxonomy.ingest.patent_cpc`
consumes the CPC Scheme archive (hierarchy + titles). This script
surfaces the parallel Full-Definition archive (definition statements,
limiting references, glossaries) into ``classification_node.description``.

The Full-Definition archive is ~900 MB extracted with one XML per
subclass; parsing the whole archive takes several minutes.

Usage:
    python -m scripts.backfill_cpc_patent_descriptions              # prod (public schema)
    python -m scripts.backfill_cpc_patent_descriptions --dry-run    # report, no UPDATE
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.cpc_patent_descriptions import (
    parse_cpc_definition_xml,
)
from world_of_taxonomy.ingest.descriptions import apply_descriptions


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_source(root: Path) -> Path:
    zips = sorted((root / "data").glob("FullCPCDefinitionXML*.zip"))
    if zips:
        return zips[-1]
    raise FileNotFoundError(
        "CPC Full-Definition archive not found. Download from "
        "https://www.cooperativepatentclassification.org/cpcBulk/ and place at "
        "data/FullCPCDefinitionXML<version>.zip"
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _find_source(root)
    print(f"  Parsing {source.name} (may take a few minutes)...")
    mapping = parse_cpc_definition_xml(source)
    print(f"  Parsed {len(mapping):,} description rows")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'patent_cpc' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null:,} CPC nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'patent_cpc' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update:,} rows")
            return 0

        updated = await apply_descriptions(conn, "patent_cpc", mapping)
        print(f"  Updated {updated:,} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'patent_cpc' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null:,} CPC nodes still have empty description")
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
