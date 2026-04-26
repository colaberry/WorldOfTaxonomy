"""Backfill descriptions for SOC 2018 aggregator nodes.

The structural ingester at :mod:`world_of_taxonomy.ingest.soc_2018`
creates four hierarchy levels:

* L1 Major Group       (e.g., 11-0000 Management Occupations)
* L2 Minor Group       (e.g., 11-1000 Top Executives)
* L3 Broad Occupation  (e.g., 11-1010 Chief Executives)
* L4 Detailed Occupation (e.g., 11-1011 Chief Executives)

The descriptions parser at
:mod:`world_of_taxonomy.ingest.soc_2018_descriptions` populates the
867 Detailed occupations from the O*NET Occupation Data file. The
BLS-published SOC definitions XLSX leaves the aggregator levels
(Major / Minor / Broad) with no SOC Definition; that's the source
itself, not a parser gap. This script composes deterministic
templated descriptions for those 268 aggregator rows from each row's
own title and its parent's title.

Usage:
    python -m scripts.backfill_soc_2018_aggregator_descriptions             # prod
    python -m scripts.backfill_soc_2018_aggregator_descriptions --dry-run   # report
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Dict, Optional

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions


def _major_description(title: str) -> str:
    return (
        f"Major occupational group ({title}) under the BLS Standard "
        f"Occupational Classification (SOC) 2018. Aggregator for "
        f"related minor groups, broad occupations, and detailed "
        f"occupations."
    )


def _minor_description(title: str, parent_title: Optional[str]) -> str:
    if not parent_title:
        return (
            f"Minor occupational group ({title}) under the BLS SOC 2018."
        )
    return (
        f"Minor occupational group ({title}) within the major group "
        f"'{parent_title}' under the BLS SOC 2018."
    )


def _broad_description(title: str, parent_title: Optional[str]) -> str:
    if not parent_title:
        return (
            f"Broad occupation category ({title}) under the BLS SOC 2018."
        )
    return (
        f"Broad occupation category ({title}) within the minor group "
        f"'{parent_title}' under the BLS SOC 2018. Aggregator of "
        f"related detailed occupations."
    )


_FILLERS = {
    1: _major_description,
    2: _minor_description,
    3: _broad_description,
}


async def _build_description_map(conn) -> Dict[str, str]:
    rows = await conn.fetch(
        """
        SELECT n.code, n.title, n.level, p.title AS parent_title
          FROM classification_node n
          LEFT JOIN classification_node p
            ON p.system_id = n.system_id AND p.code = n.parent_code
         WHERE n.system_id = 'soc_2018'
           AND n.is_leaf = false
           AND n.level IN (1, 2, 3)
           AND (n.description IS NULL OR n.description = '')
        """
    )
    out: Dict[str, str] = {}
    for r in rows:
        title = (r["title"] or "").strip()
        if not title:
            continue
        filler = _FILLERS.get(r["level"])
        if filler is None:
            continue
        if r["level"] == 1:
            out[r["code"]] = filler(title)
        else:
            parent = (r["parent_title"] or "").strip() or None
            out[r["code"]] = filler(title, parent)
    return out


async def _run(*, dry_run: bool) -> int:
    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        code_to_desc = await _build_description_map(conn)
        print(f"  Composed {len(code_to_desc):,} aggregator descriptions")
        if dry_run:
            print(f"  Would update: {len(code_to_desc):,} rows")
            return 0
        updated = await apply_descriptions(conn, "soc_2018", code_to_desc)
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
