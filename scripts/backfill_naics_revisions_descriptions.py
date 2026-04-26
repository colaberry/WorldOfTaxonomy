"""Backfill NAICS 2017 and NAICS 2012 sector skeleton descriptions.

Both systems are 21-row historical skeletons of the NAICS 2022 sector
list (one root + 20 two-digit sectors). The structural ingester
populates code + title only; the canonical Census Bureau publications
focus on the current revision (NAICS 2022), so historical skeletons
stay empty.

This script composes deterministic templated descriptions per row,
referencing the revision year and noting that the sector definitions
are aligned with the contemporaneous NAICS Manual.

Usage:
    python -m scripts.backfill_naics_revisions_descriptions             # prod
    python -m scripts.backfill_naics_revisions_descriptions --dry-run   # report
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Dict

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions


_REVISIONS = {
    "naics_2017": "2017",
    "naics_2012": "2012",
}


def _root_description(year: str) -> str:
    return (
        f"NAICS {year} top-level skeleton: aggregator of the 20 "
        f"two-digit sector codes published in the {year} edition of "
        f"the North American Industry Classification System (NAICS) "
        f"by the US Census Bureau, Statistics Canada, and INEGI Mexico."
    )


def _sector_description(year: str, title: str) -> str:
    return (
        f"NAICS {year} sector ({title}). Sector definitions in this "
        f"edition follow the {year} NAICS Manual; subsequent revisions "
        f"may have moved or renamed industries below the 2-digit level."
    )


async def _build_description_map(conn, system_id: str, year: str) -> Dict[str, str]:
    rows = await conn.fetch(
        """
        SELECT code, title, level FROM classification_node
        WHERE system_id = $1
          AND (description IS NULL OR description = '')
        """,
        system_id,
    )
    out: Dict[str, str] = {}
    for r in rows:
        title = (r["title"] or "").strip()
        if not title:
            continue
        if r["level"] == 1:
            out[r["code"]] = _root_description(year)
        else:
            out[r["code"]] = _sector_description(year, title)
    return out


async def _run(*, dry_run: bool) -> int:
    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        total = 0
        for system_id, year in _REVISIONS.items():
            code_to_desc = await _build_description_map(conn, system_id, year)
            print(f"  {system_id}: composed {len(code_to_desc)} descriptions")
            if dry_run:
                print(f"    Would update: {len(code_to_desc)} rows")
                continue
            updated = await apply_descriptions(
                conn, system_id, code_to_desc,
            )
            print(f"    Updated: {updated} rows")
            total += updated
        if not dry_run:
            print(f"\n  Total updated: {total} rows")
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
