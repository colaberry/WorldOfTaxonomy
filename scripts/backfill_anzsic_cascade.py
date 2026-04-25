"""Cascade ANZSIC 2006 child descriptions up to empty parent aggregates.

Iterates from the longest code length down, so newly populated parents
become candidates for cascading further up the hierarchy in a single
script run.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.anzsic_cascade import build_parent_mapping
from world_of_taxonomy.ingest.descriptions import apply_descriptions

_SYSTEM_ID = "anzsic_2006"


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
        # Walk lengths from longest down to shortest so each pass picks
        # up newly populated children.
        max_len = await conn.fetchval(
            "SELECT MAX(LENGTH(code)) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}'"
        )
        total_updated = 0
        for parent_len in range(max_len - 1, 0, -1):
            empty_parents = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' AND LENGTH(code) = $1 "
                "AND (description IS NULL OR description = '')",
                parent_len,
            )
            if not empty_parents:
                continue
            populated_children = await conn.fetch(
                "SELECT code, description FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' AND LENGTH(code) = $1 "
                "AND description IS NOT NULL AND description <> ''",
                parent_len + 1,
            )
            child_map = {r["code"]: r["description"] for r in populated_children}
            mapping = build_parent_mapping(
                [r["code"] for r in empty_parents], child_map,
            )
            if not mapping:
                continue
            if dry_run:
                print(
                    f"  parent_len={parent_len}: would update "
                    f"{len(mapping)} of {len(empty_parents)} empty parents"
                )
                total_updated += len(mapping)
                continue
            updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
            total_updated += updated
            print(f"  parent_len={parent_len}: updated {updated}")

        if not dry_run:
            after = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "AND (description IS NULL OR description = '')"
            )
            print(f"  Total updated: {total_updated}; still empty: {after}")
        else:
            print(f"  Total would-update: {total_updated}")
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
