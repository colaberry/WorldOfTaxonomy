"""Produce a delta data dump of classification_system + classification_node
+ equivalence for systems whose source_date >= --since.

The output is a single .sql file the CI/CD operator can apply with:

    psql -h <prod-host> -U <prod-user> -d <prod-db> -f <delta-file>

Or if gzipped:

    gunzip -c <delta-file>.gz | psql -h <prod-host> -U <prod-user> -d <prod-db>

The script wraps everything in a transaction and uses
INSERT ... ON CONFLICT ... DO UPDATE so the dump is idempotent and
additive: re-applying the same delta is a no-op, and the dump never
deletes prod rows that aren't in the delta.

Columns excluded from the dump:
  classification_system: created_at  (let prod fill from DEFAULT NOW())
  classification_node:   id, search_vector, created_at
  equivalence:           id, created_at

`node_count` on classification_system IS included (cheaper than letting
prod recompute on a 80K+-node ingester like wordnet_nouns).
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import os
import sys
from pathlib import Path

import asyncpg  # type: ignore


SYS_COLS = [
    "id",
    "name",
    "full_name",
    "region",
    "version",
    "authority",
    "url",
    "tint_color",
    "node_count",
    "source_url",
    "source_date",
    "data_provenance",
    "license",
    "source_file_hash",
    "node_url_template",
]

NODE_COLS = [
    "system_id",
    "code",
    "title",
    "description",
    "level",
    "parent_code",
    "sector_code",
    "is_leaf",
    "seq_order",
]

EQ_COLS = [
    "source_system",
    "source_code",
    "target_system",
    "target_code",
    "match_type",
    "notes",
]


def _quote_literal(value):
    """Render a Python value as a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return f"'{value.isoformat()}'"
    if isinstance(value, datetime.datetime):
        return f"'{value.isoformat()}'"
    s = str(value)
    s = s.replace("'", "''")
    return f"'{s}'"


def _row_tuple(record, cols):
    return "(" + ", ".join(_quote_literal(record[c]) for c in cols) + ")"


def _conflict_update(cols, conflict_cols):
    sets = [
        f"{c} = EXCLUDED.{c}" for c in cols if c not in conflict_cols
    ]
    return ", ".join(sets)


async def _emit_table(out, *, label, rows, table, cols, conflict_target, batch=400, conflict_action="DO UPDATE"):
    """Emit batched INSERT ... ON CONFLICT statements for a result set."""
    out.write(f"\n-- {label}: {len(rows)} rows\n")
    if not rows:
        return
    if conflict_action == "DO UPDATE":
        update_clause = _conflict_update(cols, conflict_target)
        if update_clause:
            on_conflict = f"ON CONFLICT ({', '.join(conflict_target)}) DO UPDATE SET {update_clause}"
        else:
            on_conflict = f"ON CONFLICT ({', '.join(conflict_target)}) DO NOTHING"
    elif conflict_action == "DO NOTHING":
        on_conflict = f"ON CONFLICT ({', '.join(conflict_target)}) DO NOTHING"
    else:
        on_conflict = ""

    col_list = ", ".join(cols)
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        out.write(f"INSERT INTO {table} ({col_list}) VALUES\n")
        out.write(",\n".join("  " + _row_tuple(r, cols) for r in chunk))
        out.write(f"\n{on_conflict};\n")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--since",
        required=True,
        help="ISO date (YYYY-MM-DD); include systems with source_date >= this.",
    )
    ap.add_argument(
        "--output",
        default=None,
        help="Output .sql path (default: data/wot_delta_<since>_<today>.sql).",
    )
    args = ap.parse_args()

    since = datetime.date.fromisoformat(args.since)
    today = datetime.date.today().isoformat()
    out_path = Path(
        args.output or f"data/wot_delta_{args.since}_to_{today}.sql"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.stderr.write("DATABASE_URL not set\n")
        sys.exit(2)

    conn = await asyncpg.connect(db_url)
    try:
        sys_rows = await conn.fetch(
            f"SELECT {', '.join(SYS_COLS)} FROM classification_system "
            "WHERE source_date >= $1 ORDER BY id",
            since,
        )
        if not sys_rows:
            sys.stderr.write(
                f"[delta] no classification_system rows with source_date >= {since}\n"
            )
            sys.exit(1)
        sys_ids = [r["id"] for r in sys_rows]

        node_rows = await conn.fetch(
            f"SELECT {', '.join(NODE_COLS)} FROM classification_node "
            "WHERE system_id = ANY($1::text[]) ORDER BY system_id, code",
            sys_ids,
        )

        eq_rows = await conn.fetch(
            f"SELECT {', '.join(EQ_COLS)} FROM equivalence "
            "WHERE source_system = ANY($1::text[]) "
            "   OR target_system = ANY($1::text[]) "
            "ORDER BY source_system, source_code, target_system, target_code",
            sys_ids,
        )
    finally:
        await conn.close()

    with out_path.open("w", encoding="utf-8") as out:
        out.write(
            f"-- World Of Taxonomy delta dump\n"
            f"-- Generated: {datetime.datetime.now().isoformat(timespec='seconds')}\n"
            f"-- Filter: classification_system.source_date >= {args.since}\n"
            f"-- Systems included ({len(sys_rows)}): {', '.join(sys_ids)}\n"
            f"-- Nodes: {len(node_rows)}\n"
            f"-- Equivalences: {len(eq_rows)}\n"
            f"--\n"
            f"-- Apply with: psql -h <host> -U <user> -d <db> -f <this-file>\n"
            f"-- The dump is additive (uses INSERT ... ON CONFLICT DO UPDATE).\n"
            f"-- Re-applying is safe; existing rows are upserted, others untouched.\n"
            f"\n"
            f"BEGIN;\n"
        )

        await _emit_table(
            out,
            label="classification_system",
            rows=sys_rows,
            table="classification_system",
            cols=SYS_COLS,
            conflict_target=["id"],
        )
        await _emit_table(
            out,
            label="classification_node",
            rows=node_rows,
            table="classification_node",
            cols=NODE_COLS,
            conflict_target=["system_id", "code"],
            batch=500,
        )
        await _emit_table(
            out,
            label="equivalence",
            rows=eq_rows,
            table="equivalence",
            cols=EQ_COLS,
            conflict_target=[
                "source_system",
                "source_code",
                "target_system",
                "target_code",
                "match_type",
            ],
            conflict_action="DO NOTHING",
        )

        out.write("\nCOMMIT;\n")

    size = out_path.stat().st_size
    print(
        f"[delta] wrote {out_path} "
        f"({size / 1024 / 1024:.1f} MiB, {size:,} bytes)"
    )
    print(f"[delta] systems={len(sys_rows)} nodes={len(node_rows)} edges={len(eq_rows)}")


if __name__ == "__main__":
    asyncio.run(main())
