"""Regenerate ``docs/handover/coverage-report.md`` from the live DB.

The handover doc tracks per-system description coverage across the
entire taxonomy graph. After every backfill PR the numbers shift, so
this script regenerates the markdown deterministically:

* Aggregate header line with grand totals.
* One row per system, alphabetical by ``system_id``, with totals,
  populated count, empty count, and coverage percentage.

Usage:

    python -m scripts.generate_coverage_report
    python -m scripts.generate_coverage_report --out docs/handover/coverage-report.md
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List

import asyncpg
from dotenv import load_dotenv


_DEFAULT_OUT = Path("docs/handover/coverage-report.md")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(*, out_path: Path) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        agg = await conn.fetchrow(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (
                       WHERE description IS NOT NULL AND description <> ''
                   ) AS populated,
                   COUNT(DISTINCT system_id) AS systems
            FROM classification_node
            """
        )
        rows = await conn.fetch(
            """
            SELECT s.id, s.full_name,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (
                       WHERE n.description IS NOT NULL AND n.description <> ''
                   ) AS populated
            FROM classification_system s
            JOIN classification_node n ON n.system_id = s.id
            GROUP BY s.id, s.full_name
            ORDER BY s.id
            """
        )
        lines: List[str] = ["# Coverage report", ""]
        lines.append(
            f"Generated automatically. Total rows in DB: "
            f"{agg['total']:,}."
        )
        lines.append("")
        cov_pct = (agg["populated"] / agg["total"] * 100) if agg["total"] else 0
        lines.append(
            f"**Aggregate**: {agg['populated']:,} populated / "
            f"{agg['total']:,} total = **{cov_pct:.2f}% coverage** "
            f"across {agg['systems']} systems."
        )
        lines.append("")
        lines.append(
            "| system_id | name | total | populated | empty | coverage |"
        )
        lines.append("|---|---|---:|---:|---:|---:|")
        for r in rows:
            empty = r["total"] - r["populated"]
            row_pct = (r["populated"] / r["total"] * 100) if r["total"] else 0
            name = (r["full_name"] or "")[:60]
            lines.append(
                f"| {r['id']} | {name} | {r['total']:,} | "
                f"{r['populated']:,} | {empty:,} | {row_pct:.1f}% |"
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  Wrote {out_path}: {len(rows)} systems, {cov_pct:.2f}% aggregate coverage")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=_DEFAULT_OUT,
        help="Output markdown path (default: docs/handover/coverage-report.md)",
    )
    args = parser.parse_args()
    out = (
        args.out if args.out.is_absolute()
        else _project_root() / args.out
    )
    return asyncio.run(_run(out_path=out))


if __name__ == "__main__":
    sys.exit(main())
