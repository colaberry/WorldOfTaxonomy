"""Backfill CPC v2.1 node descriptions from the UNSD explanatory-notes XLSX.

The structural ingester at :mod:`world_of_taxonomy.ingest.cpc_v21`
loads code + title from ``CPC_Ver_2_1_english_structure.txt``. UNSD
publishes a separate spreadsheet
(``CPC_Ver_2.1_Exp_Notes_Updated_<date>.xlsx``) with per-code
inclusion + exclusion paragraphs. This script surfaces those into
``classification_node.description`` (NULL-only).

Usage:
    python -m scripts.backfill_cpc_v21_descriptions               # prod
    python -m scripts.backfill_cpc_v21_descriptions --dry-run     # report only
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.cpc_v21_descriptions import (
    parse_cpc_v21_exp_notes_xlsx,
)
from world_of_taxonomy.ingest.descriptions import apply_descriptions


_DEFAULT_XLSX = Path("data/cpc_v21_exp_notes.xlsx")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_xlsx(root: Path) -> Path:
    direct = root / _DEFAULT_XLSX
    if direct.exists():
        return direct
    candidates = sorted((root / "data").glob("CPC_Ver_2.1_Exp_Notes*.xlsx"))
    if candidates:
        return candidates[-1]
    raise FileNotFoundError(
        "CPC v2.1 explanatory notes XLSX not found. Download from "
        "https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/"
        "CPC_Ver_2.1_Exp_Notes_Updated_3Apr2025.xlsx "
        f"and place it at {_DEFAULT_XLSX}"
    )


async def _run(*, dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    xlsx = _find_xlsx(root)
    print(f"  Source: {xlsx.relative_to(root)}")

    code_to_desc = parse_cpc_v21_exp_notes_xlsx(xlsx)
    print(f"  Parsed {len(code_to_desc):,} descriptions")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        if dry_run:
            empty = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id = 'cpc_v21' "
                "  AND (description IS NULL OR description = '')"
            )
            empty_codes = {r["code"] for r in empty}
            would_fill = sum(1 for c in code_to_desc if c in empty_codes)
            print(f"  Would update: {would_fill:,} rows")
            return 0
        updated = await apply_descriptions(conn, "cpc_v21", code_to_desc)
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
