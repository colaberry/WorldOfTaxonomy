"""Backfill SOC 2018 node descriptions from O*NET occupation data.

The BLS SOC 2018 XLSX definitions file is not directly downloadable
without a browser-level request, so this backfill sources descriptions
from the O*NET occupation data file (tab-delimited) that BLS/DOL
co-publishes. Only the 867 SOC 6-digit (detailed occupation) rows are
covered; Major Group, Minor Group, and Broad Occupation levels will
remain NULL.

Usage:
    python -m scripts.backfill_soc_2018_descriptions
    python -m scripts.backfill_soc_2018_descriptions --dry-run
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
from world_of_taxonomy.ingest.soc_2018_descriptions import (
    parse_soc_2018_descriptions_txt,
)


_ONET_LOCAL = Path("data/onet_occupation_data.txt")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(dry_run: bool) -> int:
    load_dotenv(_project_root() / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    txt_path = _project_root() / _ONET_LOCAL
    if not txt_path.exists():
        print(f"ERROR: {txt_path} not found. Run the O*NET ingester first.", file=sys.stderr)
        return 1

    mapping = parse_soc_2018_descriptions_txt(txt_path)
    print(f"  Parsed {len(mapping)} description rows from {txt_path.name}")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'soc_2018' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null} SOC 2018 nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'soc_2018' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update} rows")
            return 0

        updated = await apply_descriptions(conn, "soc_2018", mapping)
        print(f"  Updated {updated} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'soc_2018' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null} SOC 2018 nodes still have empty description")
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
