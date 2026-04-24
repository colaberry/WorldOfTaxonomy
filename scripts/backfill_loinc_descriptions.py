"""Backfill LOINC node descriptions from the Regenstrief LoincTable CSV.

The structural ingester at :mod:`world_of_taxonomy.ingest.loinc` only
pulls LOINC_NUM + LONG_COMMON_NAME. This script surfaces the six-axis
structure (Component, Property, Time aspect, System, Scale, Method),
the short name, and the free-text DefinitionDescription prose into
``classification_node.description``.

The LOINC release is gated behind a free Regenstrief registration and
may not be redistributed; the ZIP is expected locally at
``data/Loinc_<version>.zip``.

Usage:
    python -m scripts.backfill_loinc_descriptions              # prod (public schema)
    python -m scripts.backfill_loinc_descriptions --dry-run    # report, no UPDATE
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
from world_of_taxonomy.ingest.loinc_descriptions import (
    parse_loinc_descriptions_csv,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_loinc_source(root: Path) -> Path:
    csv_path = root / "data" / "loinc.csv"
    if csv_path.exists():
        return csv_path
    zips = sorted((root / "data").glob("Loinc_*.zip"))
    if zips:
        return zips[-1]
    raise FileNotFoundError(
        "LOINC data not found. Download from https://loinc.org/downloads/loinc-table/ "
        "(free registration required) and place the ZIP at data/Loinc_<version>.zip "
        "or extract Loinc.csv to data/loinc.csv"
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _find_loinc_source(root)
    mapping = parse_loinc_descriptions_csv(source)
    print(f"  Parsed {len(mapping):,} description rows from {source.name}")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'loinc' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null:,} LOINC nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'loinc' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update:,} rows")
            return 0

        updated = await apply_descriptions(conn, "loinc", mapping)
        print(f"  Updated {updated:,} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'loinc' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null:,} LOINC nodes still have empty description")
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
