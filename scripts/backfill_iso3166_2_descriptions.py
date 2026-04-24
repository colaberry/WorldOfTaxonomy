"""Backfill ISO 3166-2 node descriptions.

Countries come from ``data/iso3166_all.csv`` (UN M.49 region +
sub-region, alpha-3 code); subdivisions come from the ``pycountry``
library (subdivision type + parent country).
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
from world_of_taxonomy.ingest.iso3166_2_descriptions import (
    parse_iso3166_2_descriptions,
)


_SOURCE = Path("data/iso3166_all.csv")
_SYSTEM_ID = "iso_3166_2"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = root / _SOURCE
    if not source.exists():
        print(f"ERROR: {source} not found", file=sys.stderr)
        return 1

    print(f"  Parsing {source.name} + pycountry...")
    mapping = parse_iso3166_2_descriptions(source)
    print(f"  Parsed {len(mapping):,} description rows")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before:,} empty rows")

        if dry_run:
            rows = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "  AND (description IS NULL OR description = '')"
            )
            would = sum(1 for r in rows if r["code"] in mapping)
            print(f"  Dry run: would update {would:,} rows")
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
