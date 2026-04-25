"""Cascade child descriptions up via the ``parent_code`` column for
ICD-11 and ATC WHO (systems whose hierarchy is not encoded in the
code string itself).

Iterates until no more rows can be cascaded (so a populated leaf
propagates up multiple levels in successive passes).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.parent_code_cascade import build_parent_mapping


_DEFAULT_SYSTEMS = ["icd_11", "atc_who"]


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _cascade_one_pass(conn, *, system_id: str) -> int:
    empty_rows = await conn.fetch(
        "SELECT code FROM classification_node "
        "WHERE system_id = $1 AND (description IS NULL OR description = '')",
        system_id,
    )
    if not empty_rows:
        return 0
    populated_rows = await conn.fetch(
        "SELECT code, parent_code, description FROM classification_node "
        "WHERE system_id = $1 "
        "AND description IS NOT NULL AND description <> ''",
        system_id,
    )
    triples = [
        (r["code"], r["parent_code"], r["description"]) for r in populated_rows
    ]
    mapping = build_parent_mapping(
        [r["code"] for r in empty_rows], triples,
    )
    if not mapping:
        return 0
    return await apply_descriptions(conn, system_id, mapping)


async def _run(dry_run: bool, systems: List[str]) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        for sid in systems:
            print(f"  {sid}:")
            total = 0
            # Iterate until no more rows are picked up
            for pass_ in range(10):
                if dry_run:
                    # Dry: count what would change in this pass without
                    # actually applying.
                    empty_rows = await conn.fetch(
                        "SELECT code FROM classification_node "
                        "WHERE system_id = $1 "
                        "AND (description IS NULL OR description = '')",
                        sid,
                    )
                    populated_rows = await conn.fetch(
                        "SELECT code, parent_code, description FROM classification_node "
                        "WHERE system_id = $1 "
                        "AND description IS NOT NULL AND description <> ''",
                        sid,
                    )
                    triples = [
                        (r["code"], r["parent_code"], r["description"])
                        for r in populated_rows
                    ]
                    mapping = build_parent_mapping(
                        [r["code"] for r in empty_rows], triples,
                    )
                    print(f"    pass {pass_+1}: would update {len(mapping)}")
                    total += len(mapping)
                    break  # dry-run only one pass (no actual writes happen)
                updated = await _cascade_one_pass(conn, system_id=sid)
                if not updated:
                    break
                print(f"    pass {pass_+1}: updated {updated}")
                total += updated
            after = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                "WHERE system_id = $1 "
                "AND (description IS NULL OR description = '')",
                sid,
            )
            print(f"    total {'would-update' if dry_run else 'updated'}: {total}; still empty: {after}")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--systems", nargs="+",
        default=_DEFAULT_SYSTEMS,
        help="Systems to cascade (default: icd_11, atc_who)",
    )
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run, systems=args.systems))


if __name__ == "__main__":
    sys.exit(main())
