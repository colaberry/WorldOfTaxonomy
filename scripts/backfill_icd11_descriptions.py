"""Backfill ICD-11 MMS node descriptions from the WHO Simple Tabulation.

The structural ingester persists only Code and Title. This script
surfaces the ``CodingNote`` free-text guidance -- coding rules like
"Use additional code if desired" or detailed diagnostic caveats --
into ``classification_node.description``.

Coverage from this source is ~1.6% of codes (the Simple Tabulation
does not carry the formal Definition / Inclusion / Exclusion blocks
that live only in the WHO ICD-11 API).

Usage:
    python -m scripts.backfill_icd11_descriptions              # prod
    python -m scripts.backfill_icd11_descriptions --dry-run    # no UPDATE
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
from world_of_taxonomy.ingest.icd11_descriptions import (
    parse_icd11_simple_tabulation,
)


_DEFAULT_ZIP = Path("data/SimpleTabulation-ICD-11-MMS-en.zip")
_SYSTEM_ID = "icd_11"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_source(root: Path) -> Path:
    direct = root / _DEFAULT_ZIP
    if direct.exists():
        return direct
    candidates = sorted((root / "data").glob("SimpleTabulation-ICD-11-MMS*.zip"))
    if candidates:
        return candidates[-1]
    raise FileNotFoundError(
        "ICD-11 MMS Simple Tabulation not found. Download from "
        "https://icd.who.int/browse/latestrelease/mms/en and place the ZIP at "
        f"{_DEFAULT_ZIP}"
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _find_source(root)
    print(f"  Parsing {source.name}...")
    mapping = parse_icd11_simple_tabulation(source)
    print(f"  Parsed {len(mapping):,} description rows")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null:,} ICD-11 nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update:,} rows")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        print(f"  Updated {updated:,} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null:,} ICD-11 nodes still have empty description")
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
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
