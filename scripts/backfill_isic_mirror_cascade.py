"""Cascade ISIC Rev 4 child descriptions up to empty parent aggregates
across the whole ISIC family.
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
from world_of_taxonomy.ingest.isic_mirror_cascade import (
    build_parent_mapping,
    isic_family_systems,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _cascade_one_system(conn, *, system_id: str, dry_run: bool) -> int:
    max_len = await conn.fetchval(
        "SELECT MAX(LENGTH(code)) FROM classification_node WHERE system_id = $1",
        system_id,
    )
    total = 0
    for parent_len in range(max_len - 1, 0, -1):
        empty_parents = await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = $1 AND LENGTH(code) = $2 "
            "AND (description IS NULL OR description = '')",
            system_id, parent_len,
        )
        if not empty_parents:
            continue
        populated_children = await conn.fetch(
            "SELECT code, description FROM classification_node "
            "WHERE system_id = $1 AND LENGTH(code) = $2 "
            "AND description IS NOT NULL AND description <> ''",
            system_id, parent_len + 1,
        )
        child_map = {r["code"]: r["description"] for r in populated_children}
        mapping = build_parent_mapping(
            [r["code"] for r in empty_parents], child_map,
        )
        if not mapping:
            continue
        if dry_run:
            total += len(mapping)
            continue
        updated = await apply_descriptions(conn, system_id, mapping)
        total += updated
    return total


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        systems = await isic_family_systems(conn)
        print(f"  ISIC family systems: {len(systems)}")
        total = 0
        for sid in systems:
            updated = await _cascade_one_system(
                conn, system_id=sid, dry_run=dry_run,
            )
            if updated:
                tag = "would-update" if dry_run else "updated"
                print(f"    {sid:20s} {tag}={updated}")
            total += updated
        print(f"\n  Total {'would-update' if dry_run else 'updated'}: {total:,}")
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
