"""Backfill CIP 2020 node descriptions from the NCES CIPCode2020.csv.

The structural ingester at `world_of_taxonomy/ingest/cip_2020.py` uses
the same CSV but only pulls the title column. The `CIPDefinition` prose
is surfaced here and written into `classification_node.description`.

Usage:
    python -m scripts.backfill_cip_2020_descriptions                 # prod (public schema)
    python -m scripts.backfill_cip_2020_descriptions --dry-run       # report, no UPDATE
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.base import ensure_data_file
from world_of_taxonomy.ingest.cip_2020_descriptions import (
    parse_cip_2020_descriptions_csv,
)
from world_of_taxonomy.ingest.descriptions import apply_descriptions


_CIP_2020_URL = "https://nces.ed.gov/ipeds/cipcode/Files/CIPCode2020.csv"
_CIP_2020_LOCAL = Path("data/cip_2020.csv")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(dry_run: bool) -> int:
    load_dotenv(_project_root() / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    csv_path = ensure_data_file(_CIP_2020_URL, _project_root() / _CIP_2020_LOCAL)
    mapping = parse_cip_2020_descriptions_csv(csv_path)
    print(f"  Parsed {len(mapping)} description rows from {csv_path.name}")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'cip_2020' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null} CIP 2020 nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'cip_2020' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update} rows")
            return 0

        updated = await apply_descriptions(conn, "cip_2020", mapping)
        print(f"  Updated {updated} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'cip_2020' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null} CIP 2020 nodes still have empty description")
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
