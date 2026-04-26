"""Mirror non-empty descriptions from a canonical system to its
structural derivatives.

Many national industrial classifications mirror an upstream UN/EU
classification 1-to-1: e.g. NACE Rev 2 has 41 EU national derivatives
(WZ, OENACE, NOGA, ATECO, NAF, ...) that share the same 996-code
hierarchy. ISIC Rev 4 has 122+ derivatives (CIIU country variants,
ISIC-AO/AE/AF/AG/...). Filling descriptions on the canonical parent
should propagate to all derivatives for free.

This script does that propagation as a NULL-only UPDATE: a derivative
row keeps any existing description and only fills empty rows from the
canonical parent's description column.

Auto-detection: by default the script picks every other system whose
node count exactly matches the canonical parent's, then verifies code
overlap is greater than ``MIN_OVERLAP`` before mirroring. The target
list can also be passed explicitly with ``--targets``.

Usage:

    python3 -m scripts.mirror_descriptions --from nace_rev2
    python3 -m scripts.mirror_descriptions --from isic_rev4 --dry-run
    python3 -m scripts.mirror_descriptions --from isic_rev4 \
        --targets ciiu_co ciiu_ar
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Iterable, List, Optional

import asyncpg
from dotenv import load_dotenv


_MIN_OVERLAP = 0.95


async def _detect_targets(conn, source: str) -> List[str]:
    """Return systems with the same node count as ``source`` (excluding
    ``source`` itself). The caller validates overlap separately.
    """
    src_total = await conn.fetchval(
        "SELECT COUNT(*) FROM classification_node WHERE system_id = $1",
        source,
    )
    if not src_total:
        return []
    rows = await conn.fetch(
        """
        SELECT system_id FROM classification_node
        GROUP BY system_id HAVING COUNT(*) = $1 AND system_id <> $2
        ORDER BY system_id
        """,
        src_total,
        source,
    )
    return [r["system_id"] for r in rows]


async def _code_overlap(conn, source: str, target: str) -> float:
    """Return the fraction of ``target`` codes that exist in ``source``."""
    r = await conn.fetchrow(
        """
        WITH t AS (SELECT code FROM classification_node WHERE system_id = $2),
             s AS (SELECT code FROM classification_node WHERE system_id = $1)
        SELECT
          (SELECT COUNT(*) FROM t WHERE code IN (SELECT code FROM s))::float
            / NULLIF((SELECT COUNT(*) FROM t), 0) AS overlap
        """,
        source,
        target,
    )
    return float(r["overlap"] or 0.0)


async def _mirror_one(
    conn, *, source: str, target: str, dry_run: bool,
) -> int:
    """Copy descriptions for matching codes where the target row is
    NULL/empty. Returns rows updated (or that would be updated).
    """
    if dry_run:
        r = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM classification_node t
            JOIN classification_node s
              ON s.system_id = $1 AND s.code = t.code
            WHERE t.system_id = $2
              AND (t.description IS NULL OR t.description = '')
              AND s.description IS NOT NULL AND s.description <> ''
            """,
            source,
            target,
        )
        return int(r or 0)
    result = await conn.execute(
        """
        UPDATE classification_node t
           SET description = s.description
          FROM classification_node s
         WHERE s.system_id = $1
           AND t.system_id = $2
           AND s.code = t.code
           AND (t.description IS NULL OR t.description = '')
           AND s.description IS NOT NULL AND s.description <> ''
        """,
        source,
        target,
    )
    return int(result.split()[-1])


async def _run(
    *, source: str, targets: Optional[List[str]], dry_run: bool,
) -> int:
    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        if targets:
            chosen = targets
        else:
            chosen = await _detect_targets(conn, source)
            if not chosen:
                print(
                    f"  No structural derivatives detected for {source}",
                    file=sys.stderr,
                )
                return 0
        print(f"  source: {source}")
        print(f"  candidates: {len(chosen)}")
        total_updated = 0
        skipped = 0
        for target in chosen:
            overlap = await _code_overlap(conn, source, target)
            if overlap < _MIN_OVERLAP:
                print(
                    f"    SKIP {target}: code overlap {overlap*100:.1f}% "
                    f"< {_MIN_OVERLAP*100:.0f}%"
                )
                skipped += 1
                continue
            n = await _mirror_one(
                conn, source=source, target=target, dry_run=dry_run,
            )
            verb = "would update" if dry_run else "updated"
            print(f"    {target}: {verb} {n} rows  (overlap {overlap*100:.0f}%)")
            total_updated += n
        verb = "Would update" if dry_run else "Updated"
        print(
            f"\n  {verb} {total_updated:,} rows across "
            f"{len(chosen) - skipped} systems"
        )
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from", dest="source", required=True,
        help="Canonical system_id whose descriptions cascade to derivatives.",
    )
    parser.add_argument(
        "--targets", nargs="*", default=None,
        help="Explicit derivative system_ids. Default: auto-detect by node count.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return asyncio.run(_run(
        source=args.source, targets=args.targets, dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    sys.exit(main())
