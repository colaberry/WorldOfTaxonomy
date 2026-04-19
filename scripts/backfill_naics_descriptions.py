"""Backfill NAICS 2022 node descriptions from the Census Bureau XLSX.

The structural ingester at `world_of_taxonomy/ingest/naics.py` uses the
2-6 digit codes file, which carries titles but no description prose.
Census publishes descriptions separately; this script downloads that
companion file and fills `classification_node.description` for every
NAICS 2022 node.

Usage:
    python -m scripts.backfill_naics_descriptions                 # prod (public schema)
    python -m scripts.backfill_naics_descriptions --dry-run       # report, no UPDATE
    python -m scripts.backfill_naics_descriptions --reset-sentinel # nullify rows whose
                                                                   # description is the
                                                                   # literal "NULL" that
                                                                   # leaked through an
                                                                   # earlier parser run
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
from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.naics_descriptions import (
    NAICS_2022_DESCRIPTIONS_LOCAL,
    NAICS_2022_DESCRIPTIONS_URL,
    parse_naics_descriptions_xlsx,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _reset_sentinel(conn) -> None:
    before = await conn.fetchval(
        "SELECT COUNT(*) FROM classification_node "
        "WHERE system_id = 'naics_2022' AND description = 'NULL'"
    )
    print(f"  Found {before} rows with literal 'NULL' description")
    result = await conn.execute(
        "UPDATE classification_node SET description = NULL "
        "WHERE system_id = 'naics_2022' AND description = 'NULL'"
    )
    print(f"  {result}")


async def _run(dry_run: bool, reset_sentinel: bool) -> int:
    load_dotenv(_project_root() / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    if reset_sentinel:
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        try:
            await _reset_sentinel(conn)
        finally:
            await conn.close()
        return 0

    xlsx_path = ensure_data_file(
        NAICS_2022_DESCRIPTIONS_URL,
        _project_root() / NAICS_2022_DESCRIPTIONS_LOCAL,
    )
    mapping = parse_naics_descriptions_xlsx(xlsx_path)
    print(f"  Parsed {len(mapping)} description rows from {xlsx_path.name}")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'naics_2022' AND description IS NULL"
        )
        print(f"  Before: {before_null} NAICS 2022 nodes have NULL description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'naics_2022' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update} rows")
            return 0

        updated = await apply_descriptions(conn, "naics_2022", mapping)
        print(f"  Updated {updated} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'naics_2022' AND description IS NULL"
        )
        print(f"  After: {after_null} NAICS 2022 nodes still have NULL description")
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
    parser.add_argument(
        "--reset-sentinel",
        action="store_true",
        help="Reset rows whose description is the literal string 'NULL' to real NULL",
    )
    args = parser.parse_args()
    return asyncio.run(
        _run(dry_run=args.dry_run, reset_sentinel=args.reset_sentinel)
    )


if __name__ == "__main__":
    sys.exit(main())
