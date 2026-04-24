"""Backfill NCI Thesaurus node descriptions from the EVS flat file.

The structural ingester at :mod:`world_of_taxonomy.ingest.nci_thesaurus`
only persists the code + display name. Columns 3, 4, and 7 of the flat
file carry synonyms, definitions, and the semantic type; this script
surfaces them as markdown into ``classification_node.description``.

Usage:
    python -m scripts.backfill_nci_thesaurus_descriptions              # prod (public schema)
    python -m scripts.backfill_nci_thesaurus_descriptions --dry-run    # report, no UPDATE
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
from world_of_taxonomy.ingest.nci_thesaurus_descriptions import (
    parse_nci_thesaurus_descriptions,
)


_DEFAULT_ZIP = Path("data/nci_thesaurus.zip")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_source(root: Path) -> Path:
    direct = root / _DEFAULT_ZIP
    if direct.exists():
        return direct
    zips = sorted(
        (root / "data").glob("*thesaurus*.zip"),
        key=lambda p: p.name.lower(),
    )
    if zips:
        return zips[-1]
    raise FileNotFoundError(
        "NCI Thesaurus data not found. Download from "
        "https://evs.nci.nih.gov/evs-download/thesaurus-downloads "
        f"and place the ZIP at {_DEFAULT_ZIP}"
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _find_source(root)
    print(f"  Parsing {source.name} (may take ~30s)...")
    mapping = parse_nci_thesaurus_descriptions(source)
    print(f"  Parsed {len(mapping):,} description rows")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'nci_thesaurus' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null:,} NCI Thesaurus nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'nci_thesaurus' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update:,} rows")
            return 0

        updated = await apply_descriptions(conn, "nci_thesaurus", mapping)
        print(f"  Updated {updated:,} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'nci_thesaurus' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null:,} NCI Thesaurus nodes still have empty description")
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
