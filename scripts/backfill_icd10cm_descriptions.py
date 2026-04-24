"""Backfill ICD-10-CM node descriptions from the CMS Tabular XML.

The structural ingester at :mod:`world_of_taxonomy.ingest.icd10cm`
loads the 97,606 codes + titles from the CMS *order* file. The
companion *Tabular* XML carries the clinician-facing notes (inclusion
terms, Excludes1/Excludes2, Use-Additional, Code-First, 7th-character
definitions). This script surfaces those notes into
``classification_node.description``.

Usage:
    python -m scripts.backfill_icd10cm_descriptions              # prod (public schema)
    python -m scripts.backfill_icd10cm_descriptions --dry-run    # report, no UPDATE
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
from world_of_taxonomy.ingest.icd10cm_descriptions import (
    parse_icd10cm_tabular_xml,
)


_DEFAULT_ZIP = Path("data/icd10cm_tabular_2025.zip")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_tabular_zip(root: Path) -> Path:
    direct = root / _DEFAULT_ZIP
    if direct.exists():
        return direct
    zips = sorted((root / "data").glob("icd10cm_tabular_*.zip"))
    if zips:
        return zips[-1]
    raise FileNotFoundError(
        "ICD-10-CM Tabular XML not found. Download from "
        "https://www.cms.gov/medicare/coding-billing/icd-10-codes "
        f"and place the ZIP at {_DEFAULT_ZIP}"
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    zip_path = _find_tabular_zip(root)
    mapping = parse_icd10cm_tabular_xml(zip_path)
    print(f"  Parsed {len(mapping):,} description rows from {zip_path.name}")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'icd10cm' AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before_null:,} ICD-10-CM nodes have empty description")

        if dry_run:
            candidates = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'icd10cm' "
                "  AND (description IS NULL OR description = '')"
            )
            would_update = sum(1 for r in candidates if r["code"] in mapping)
            print(f"  Dry run: would update {would_update:,} rows")
            return 0

        updated = await apply_descriptions(conn, "icd10cm", mapping)
        print(f"  Updated {updated:,} rows")

        after_null = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            "WHERE system_id = 'icd10cm' AND (description IS NULL OR description = '')"
        )
        print(f"  After: {after_null:,} ICD-10-CM nodes still have empty description")
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
