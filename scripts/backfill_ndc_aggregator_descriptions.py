"""Backfill descriptions for the synthesized NDC aggregator nodes.

The structural ingester at :mod:`world_of_taxonomy.ingest.ndc_fda`
emits two layers of synthetic aggregator nodes that do not appear in
the FDA product file:

* L1 marketing categories: ``NDC-RX`` (Human Prescription Drug),
  ``NDC-OTC`` (Human OTC Drug), ``NDC-VAC`` (Vaccine),
  ``NDC-ALG`` / ``NDC-SAL`` (Allergenics), ``NDC-CEL`` (Cellular
  Therapy).
* L2 dosage form aggregators inside each category: ``NDC-OTC.CAPSULE``,
  ``NDC-RX.SOLUTION``, etc.

The product-file parser (``ndc_fda_descriptions.py``) covers leaf
products via ``product.txt``. These aggregators have no source
record, so this script composes deterministic templated descriptions
from each aggregator's title plus its parent's title.

Usage:
    python -m scripts.backfill_ndc_aggregator_descriptions             # prod
    python -m scripts.backfill_ndc_aggregator_descriptions --dry-run   # report
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


def _l1_description(title: str) -> str:
    return (
        f"FDA marketing category aggregator for {title} products. "
        f"Sub-nodes group products in this category by dosage form."
    )


def _l2_description(title: str, parent_title: Optional[str]) -> str:
    if not parent_title:
        return (
            f"FDA dosage form aggregator: {title}. Groups products that "
            f"share this dosage form."
        )
    return (
        f"{title} dosage form aggregator within the FDA marketing "
        f"category '{parent_title}'."
    )


async def _build_description_map(conn) -> Dict[str, str]:
    rows = await conn.fetch(
        """
        SELECT n.code, n.title, n.level, n.parent_code, p.title AS parent_title
          FROM classification_node n
          LEFT JOIN classification_node p
            ON p.system_id = n.system_id AND p.code = n.parent_code
         WHERE n.system_id = 'ndc_fda'
           AND n.is_leaf = false
           AND (n.description IS NULL OR n.description = '')
        """
    )
    out: Dict[str, str] = {}
    for r in rows:
        title = (r["title"] or "").strip()
        if not title:
            continue
        if r["level"] == 1:
            out[r["code"]] = _l1_description(title)
        elif r["level"] == 2:
            out[r["code"]] = _l2_description(
                title, (r["parent_title"] or "").strip() or None,
            )
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
        updated = await apply_descriptions(conn, "ndc_fda", code_to_desc)
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
