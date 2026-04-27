"""Backfill ANZSIC 2006 node descriptions.

Two passes:

1. Authoritative SDMX descriptions (ABS codelist XML) for codes that
   carry a non-empty <common:Description>. Covers Divisions and many
   class-level rows; the structural ingester usually picks these up,
   but a small tail (~11 rows) still benefits.
2. Templated descriptions for remaining empty Subdivision and Group
   aggregator rows, composed from each row's title and its parent's
   title. ABS does not publish per-Subdivision / per-Group prose in
   the SDMX feed.

Usage:
    python -m scripts.backfill_anzsic_2006_descriptions             # prod
    python -m scripts.backfill_anzsic_2006_descriptions --dry-run   # report
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.anzsic_2006_descriptions import (
    parse_anzsic_2006_descriptions,
)
from world_of_taxonomy.ingest.descriptions import apply_descriptions


_DEFAULT_XML = Path("data/anzsic_2006.xml")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _subdivision_description(title: str, parent_title: str) -> str:
    if not parent_title:
        return f"Subdivision ({title}) under ANZSIC 2006."
    return (
        f"Subdivision ({title}) within the division '{parent_title}' "
        f"under ANZSIC 2006."
    )


def _group_description(title: str, parent_title: str) -> str:
    if not parent_title:
        return f"Group ({title}) under ANZSIC 2006."
    return (
        f"Group ({title}) within the subdivision '{parent_title}' "
        f"under ANZSIC 2006."
    )


_TEMPLATE_BY_LEVEL = {
    1: _subdivision_description,
    2: _group_description,
}


async def _build_aggregator_map(conn) -> dict:
    rows = await conn.fetch(
        """
        SELECT n.code, n.title, n.level, p.title AS parent_title
          FROM classification_node n
          LEFT JOIN classification_node p
            ON p.system_id = n.system_id AND p.code = n.parent_code
         WHERE n.system_id = 'anzsic_2006'
           AND n.level IN (1, 2)
           AND (n.description IS NULL OR n.description = '')
        """
    )
    out = {}
    for r in rows:
        title = (r["title"] or "").strip()
        if not title:
            continue
        filler = _TEMPLATE_BY_LEVEL.get(r["level"])
        if filler is None:
            continue
        out[r["code"]] = filler(title, (r["parent_title"] or "").strip())
    return out


async def _run(*, dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    xml = root / _DEFAULT_XML
    if not xml.exists():
        print(
            f"ERROR: {_DEFAULT_XML} missing. Download from "
            "https://api.data.abs.gov.au/codelist/ABS/CL_ANZSIC_2006/1.0.0",
            file=sys.stderr,
        )
        return 1
    code_to_desc = parse_anzsic_2006_descriptions(xml)
    print(f"  Source: {_DEFAULT_XML}")
    print(f"  Pass 1 (authoritative): parsed {len(code_to_desc):,} entries")
    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        if dry_run:
            empty = await conn.fetch(
                "SELECT code FROM classification_node "
                "WHERE system_id='anzsic_2006' "
                "  AND (description IS NULL OR description = '')"
            )
            empty_codes = {r["code"] for r in empty}
            would_p1 = sum(1 for c in code_to_desc if c in empty_codes)
            templates = await _build_aggregator_map(conn)
            print(f"  Pass 1 would update: {would_p1:,} rows")
            print(
                f"  Pass 2 (templates) would update: "
                f"{len(templates):,} rows"
            )
            return 0
        p1_updated = await apply_descriptions(
            conn, "anzsic_2006", code_to_desc,
        )
        print(f"  Pass 1 applied: {p1_updated:,} rows")
        templates = await _build_aggregator_map(conn)
        p2_updated = await apply_descriptions(
            conn, "anzsic_2006", templates,
        )
        print(f"  Pass 2 (templates) applied: {p2_updated:,} rows")
        print(f"  Total updated: {p1_updated + p2_updated:,} rows")
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
