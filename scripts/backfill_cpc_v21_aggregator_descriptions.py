"""Backfill CPC v2.1 aggregator descriptions for codes UNSD does not
publish inclusion/exclusion paragraphs for.

The XLSX-based backfill (2824f44) covered 2,633 rows with rich
inclusion + exclusion notes. The remaining 1,963 empty rows are
codes UNSD publishes only as ``code -> title``. This script composes
deterministic templated descriptions per hierarchy level
(Section / Division / Group / Class / Subclass) from each row's
title and its parent's title.

Usage:
    python -m scripts.backfill_cpc_v21_aggregator_descriptions             # prod
    python -m scripts.backfill_cpc_v21_aggregator_descriptions --dry-run   # report
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


_LEVEL_LABELS = {
    1: "section",
    2: "division",
    3: "group",
    4: "class",
    5: "subclass",
}


def _description(
    level: int, title: str, parent_title: Optional[str],
) -> str:
    label = _LEVEL_LABELS.get(level, "code")
    if level == 1 or not parent_title:
        return (
            f"CPC v2.1 {label}: {title}. UN Central Product "
            f"Classification grouping of related products."
        )
    return (
        f"CPC v2.1 {label} ({title}) within '{parent_title}'. "
        f"UN Central Product Classification grouping of related "
        f"products at this level."
    )


async def _build_description_map(conn) -> Dict[str, str]:
    rows = await conn.fetch(
        """
        SELECT n.code, n.title, n.level, p.title AS parent_title
          FROM classification_node n
          LEFT JOIN classification_node p
            ON p.system_id=n.system_id AND p.code=n.parent_code
         WHERE n.system_id='cpc_v21'
           AND (n.description IS NULL OR n.description='')
        """
    )
    out: Dict[str, str] = {}
    for r in rows:
        title = (r["title"] or "").strip()
        if not title:
            continue
        parent = (r["parent_title"] or "").strip() or None
        out[r["code"]] = _description(r["level"], title, parent)
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
