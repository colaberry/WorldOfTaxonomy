"""Cascade ISCED-F 2013 child descriptions to empty parent aggregates.

For every empty 2-digit broad field or 3-digit narrow field with
exactly one populated direct child, copy the child's description up
to the parent.
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
from world_of_taxonomy.ingest.iscedf_cascade import build_parent_mapping

_SYSTEM_ID = "iscedf_2013"


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
        empty_parents = await conn.fetch(
            "SELECT code FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        empty_codes = [r["code"] for r in empty_parents]
        print(f"  Empty rows: {len(empty_codes):,}")

        populated = await conn.fetch(
            "SELECT code, description FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND description IS NOT NULL AND description <> ''"
        )
        populated_map = {r["code"]: r["description"] for r in populated}
        print(f"  Populated rows (source for cascade): {len(populated_map):,}")

        mapping = build_parent_mapping(empty_codes, populated_map)
        print(f"  Cascade candidates: {len(mapping):,}")

        if dry_run:
            for k, v in list(mapping.items())[:5]:
                print(f"    {k} -> {v[:80]}")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Updated {updated:,} rows; still-empty {after:,}")
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
