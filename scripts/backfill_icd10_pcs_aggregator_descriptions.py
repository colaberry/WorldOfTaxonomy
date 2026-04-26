"""Backfill ICD-10-PCS aggregator descriptions (L1 sections, L2 body
systems, L3 root-op tables without inline definitions, and L4 leaves
under those tables).

The Tables-XML backfill (fb76071) covered ~77K rows whose 3-char
prefix had a ``<definition>`` element on the operation axis. The
remaining empty rows split across:

* 17 L1 sections (e.g., ``0`` Medical and Surgical) - section codes
  themselves have no definition in any CMS file.
* 114 L2 body systems (e.g., ``00`` Central Nervous System and
  Cranial Nerves) - synthesized aggregators with no source row.
* 56 L3 root-op tables in Section D (Radiation Therapy) and a few
  other sections that are absent from
  ``icd10pcs_definitions_2025.xml`` and skipped by the Tables-XML
  parser (no ``<definition>`` element on the operation axis).
* 2,056 L4 leaves under those 56 L3 tables - inherit the same gap.

This script composes deterministic templated descriptions from each
row's title and its parent's title. L4 leaves cascade their L3
parent's templated description, mirroring the cascade behavior of
the original Tables-XML pass.

Usage:
    python -m scripts.backfill_icd10_pcs_aggregator_descriptions             # prod
    python -m scripts.backfill_icd10_pcs_aggregator_descriptions --dry-run   # report
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


def _section_description(title: str) -> str:
    return (
        f"ICD-10-PCS section ({title}). Top-level grouping of "
        f"procedure codes; sub-nodes break down by body system, "
        f"operation, and detailed code."
    )


def _body_system_description(title: str, section_title: Optional[str]) -> str:
    if section_title:
        return (
            f"Body system ({title}) within ICD-10-PCS section "
            f"'{section_title}'. Aggregator of root-operation tables "
            f"for this body system."
        )
    return (
        f"Body system ({title}) under ICD-10-PCS. Aggregator of "
        f"root-operation tables."
    )


def _table_description(title: str, body_system_title: Optional[str]) -> str:
    if body_system_title:
        return (
            f"ICD-10-PCS root-operation table: {title}. Body system: "
            f"{body_system_title}."
        )
    return f"ICD-10-PCS root-operation table: {title}."


async def _build_description_map(conn) -> Dict[str, str]:
    out: Dict[str, str] = {}

    # L1: sections
    rows = await conn.fetch(
        "SELECT code, title FROM classification_node "
        "WHERE system_id='icd10_pcs' AND level=1 "
        "  AND (description IS NULL OR description='')"
    )
    for r in rows:
        title = (r["title"] or "").strip()
        if title:
            out[r["code"]] = _section_description(title)

    # L2: body systems (parent = section)
    rows = await conn.fetch(
        """
        SELECT n.code, n.title, p.title AS parent_title
          FROM classification_node n
          LEFT JOIN classification_node p
            ON p.system_id=n.system_id AND p.code=n.parent_code
         WHERE n.system_id='icd10_pcs' AND n.level=2
           AND (n.description IS NULL OR n.description='')
        """
    )
    for r in rows:
        title = (r["title"] or "").strip()
        if title:
            out[r["code"]] = _body_system_description(
                title, (r["parent_title"] or "").strip() or None,
            )

    # L3: root-op tables without inline definition. Parent is L2 body
    # system, but we want the body system title (which the L2 stored
    # before being filled). Use a self-join on n.parent_code.
    rows = await conn.fetch(
        """
        SELECT n.code, n.title, p.title AS parent_title
          FROM classification_node n
          LEFT JOIN classification_node p
            ON p.system_id=n.system_id AND p.code=n.parent_code
         WHERE n.system_id='icd10_pcs' AND n.level=3
           AND (n.description IS NULL OR n.description='')
        """
    )
    l3_descriptions = {}
    for r in rows:
        title = (r["title"] or "").strip()
        if title:
            d = _table_description(
                title, (r["parent_title"] or "").strip() or None,
            )
            out[r["code"]] = d
            l3_descriptions[r["code"]] = d

    # L4: leaves under empty L3 tables - cascade the templated L3 description
    if l3_descriptions:
        leaves = await conn.fetch(
            """
            SELECT code FROM classification_node
            WHERE system_id='icd10_pcs' AND level=4
              AND (description IS NULL OR description='')
              AND LEFT(code, 3) = ANY($1::text[])
            """,
            list(l3_descriptions.keys()),
        )
        for r in leaves:
            prefix = r["code"][:3]
            if prefix in l3_descriptions:
                out[r["code"]] = l3_descriptions[prefix]

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
        print(
            f"  Composed {len(code_to_desc):,} aggregator/cascade "
            f"descriptions"
        )
        if dry_run:
            print(f"  Would update: {len(code_to_desc):,} rows")
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
