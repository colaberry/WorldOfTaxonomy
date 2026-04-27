"""Cascade NACE Rev 2 class descriptions up to empty group parents.

For every system in the NACE family (detected by membership of the
canonical 4-digit class ``01.11``), fill empty groups (``XX.X``) whose
single class child (``XX.XX``) already has a description.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.nace_group_cascade import build_group_mapping


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _nace_family(conn) -> List[str]:
    rows = await conn.fetch(
        "SELECT DISTINCT system_id FROM classification_node "
        "WHERE code = '01.11' ORDER BY system_id"
    )
    return [r["system_id"] for r in rows]


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        systems = await _nace_family(conn)
        print(f"  NACE-family systems: {len(systems)}")

        total_updated = 0
        for sid in systems:
            empty_groups = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = $1 AND LENGTH(code) = 4 "
                "AND (description IS NULL OR description = '')",
                sid,
            )
            group_codes = [r["code"] for r in empty_groups]
            if not group_codes:
                continue

            populated_classes = await conn.fetch(
                "SELECT code, description FROM classification_node "
                "WHERE system_id = $1 AND LENGTH(code) = 5 "
                "AND description IS NOT NULL AND description <> ''",
                sid,
            )
            class_map = {r["code"]: r["description"] for r in populated_classes}

            mapping = build_group_mapping(group_codes, class_map)
            if not mapping:
                continue

            if dry_run:
                print(f"    {sid:20s} empty-groups={len(group_codes):>3} would-update={len(mapping):>3}")
                total_updated += len(mapping)
                continue

            updated = await apply_descriptions(conn, sid, mapping)
            after_empty = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                "WHERE system_id = $1 AND LENGTH(code) = 4 "
                "AND (description IS NULL OR description = '')",
                sid,
            )
            print(f"    {sid:20s} updated={updated:>3}  groups-still-empty={after_empty:>3}")
            total_updated += updated
        print(f"  Total updated across systems: {total_updated:,}")
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
