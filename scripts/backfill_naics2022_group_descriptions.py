"""Backfill NAICS 2022 industry-group (4-digit) descriptions by cascading
from the resolved 5-digit / 6-digit child description.
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
from world_of_taxonomy.ingest.naics2022_cascade import resolve_description

_SYSTEM_ID = "naics_2022"


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
        # Load full description map for pointer resolution
        all_rows = await conn.fetch(
            "SELECT code, description FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}'"
        )
        code_desc = {r["code"]: (r["description"] or "") for r in all_rows}

        # Empty 4-digit groups
        empty_groups = await conn.fetch(
            "SELECT code FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND LENGTH(code) = 4 "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Empty 4-digit groups: {len(empty_groups):,}")

        mapping: dict[str, str] = {}
        for row in empty_groups:
            group_code = row["code"]
            # Find the 5-digit children whose first 4 chars match
            children = [
                c for c in code_desc
                if len(c) == 5 and c.startswith(group_code)
            ]
            if len(children) != 1:
                continue
            child_code = children[0]
            resolved = resolve_description(child_code, code_desc)
            if resolved:
                mapping[group_code] = resolved

        print(f"  Groups with resolvable child description: {len(mapping):,}")

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
