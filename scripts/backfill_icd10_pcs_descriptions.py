"""Backfill ICD-10-PCS node descriptions from the CMS Tables XML.

The structural ingester at :mod:`world_of_taxonomy.ingest.icd10_pcs`
loads ~80K codes + titles from the CMS order file but does not
populate descriptions. The companion Tables XML embeds an operation
``<definition>`` for each 3-char root operation table, which is the
natural per-code description: every leaf under a 3-char prefix shares
that prefix's operation, so the operation definition applies to the
3-char node and its leaves uniformly.

Usage:
    python -m scripts.backfill_icd10_pcs_descriptions              # prod (public schema)
    python -m scripts.backfill_icd10_pcs_descriptions --dry-run    # report, no UPDATE
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
from world_of_taxonomy.ingest.icd10_pcs_descriptions import (
    parse_icd10pcs_tables_xml,
)


_DEFAULT_ZIP = Path("data/icd10pcs_tables_2025.zip")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_tables_zip(root: Path) -> Path:
    direct = root / _DEFAULT_ZIP
    if direct.exists():
        return direct
    zips = sorted((root / "data").glob("icd10pcs_tables_*.zip"))
    if zips:
        return zips[-1]
    raise FileNotFoundError(
        "ICD-10-PCS Tables XML not found. Download from "
        "https://www.cms.gov/medicare/coding-billing/icd-10-codes "
        f"and place the ZIP at {_DEFAULT_ZIP}"
    )


async def _run(*, dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    zip_path = _find_tables_zip(root)
    print(f"  Source: {zip_path.relative_to(root)}")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        leaves = await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'icd10_pcs' AND LENGTH(code) = 7"
        )
        leaf_codes = [r["code"] for r in leaves]

        code_to_desc = parse_icd10pcs_tables_xml(
            zip_path, leaf_codes=leaf_codes,
        )
        print(
            f"  Parsed {len(code_to_desc):,} descriptions "
            f"({sum(1 for c in code_to_desc if len(c) == 3):,} root-op tables, "
            f"{sum(1 for c in code_to_desc if len(c) == 7):,} leaves)"
        )

        if dry_run:
            empty = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'icd10_pcs' "
                "  AND (description IS NULL OR description = '')"
            )
            empty_codes = {r["code"] for r in empty}
            would_fill = sum(1 for c in code_to_desc if c in empty_codes)
            print(f"  Would update: {would_fill:,} rows")
            return 0

        updated = await apply_descriptions(conn, "icd10_pcs", code_to_desc)
        print(f"  Updated: {updated:,} rows")
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
