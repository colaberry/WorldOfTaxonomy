"""Backfill Patent CPC descriptions from the FullCPCDefinitionXML zip.

Source: ``data/FullCPCDefinitionXML202601.zip`` (24,233 XML files,
~935 MB uncompressed). Each ``<definition-item>`` carries
structured Definition / Limiting References / Glossary content
that the lighter Scheme-XML parser (PR #73) does not include.
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
from world_of_taxonomy.ingest.patent_cpc_full_definition import (
    parse_definition_zip,
)


_SOURCE = Path("data/FullCPCDefinitionXML202601.zip")
_SYSTEM_ID = "patent_cpc"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    src = root / _SOURCE
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        return 1

    print(f"  Parsing {src.name} (this takes ~30s)...")
    mapping = parse_definition_zip(src)
    print(f"  Extracted definitions for {len(mapping):,} CPC items")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before:,} empty rows")

        if dry_run:
            empty_codes = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "AND (description IS NULL OR description = '')"
            )
            would = sum(1 for r in empty_codes if r["code"] in mapping)
            in_db = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "AND code = ANY($1::text[])",
                list(mapping.keys()),
            )
            print(f"  Dry run: would update {would:,} rows; "
                  f"{in_db:,} of {len(mapping):,} extracted codes match a DB row")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Updated {updated:,} rows; still empty {after:,}")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
