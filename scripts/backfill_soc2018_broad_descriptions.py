"""Backfill SOC 2018 broad-occupation descriptions from populated detailed
occupations.

Applies to empty level-3 (broad) SOC rows where exactly one detailed
child already has a description. Broads with multiple detailed children
are intentionally left empty.
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
from world_of_taxonomy.ingest.soc2018_cascade import build_broad_mapping

_SYSTEM_ID = "soc_2018"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        empty_broads = await conn.fetch(
            "SELECT code FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND level = 3 "
            "AND (description IS NULL OR description = '')"
        )
        broad_codes = [r["code"] for r in empty_broads]
        print(f"  Empty broad occupations: {len(broad_codes):,}")

        populated_detailed = await conn.fetch(
            "SELECT code, description FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND level = 4 "
            "AND description IS NOT NULL AND description <> ''"
        )
        detailed_map = {r["code"]: r["description"] for r in populated_detailed}
        print(f"  Populated detailed occupations: {len(detailed_map):,}")

        mapping = build_broad_mapping(broad_codes, detailed_map)
        print(f"  Broads with exactly-one-child: {len(mapping):,}")

        if dry_run:
            print(f"  Dry run: would update {len(mapping):,} rows")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Updated {updated:,} rows, {after:,} still empty")
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
