"""Backfill ESCO occupation + skill descriptions from the JSON-LD dump.

The structural ingester persists only the preferred English label. This
script surfaces the ``skos:definition`` / ``dct:description`` field
(whichever ESCO provides for the concept) into
``classification_node.description``, keyed by the UUID portion of the
concept URI.

Usage:
    python -m scripts.backfill_esco_descriptions --dry-run
    python -m scripts.backfill_esco_descriptions             # both
    python -m scripts.backfill_esco_descriptions --only occupations
    python -m scripts.backfill_esco_descriptions --only skills
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.esco_descriptions import parse_esco_descriptions


_TARGETS = {
    "occupations": ("esco_occupations", "occupation"),
    "skills": ("esco_skills", "skill"),
}

_DEFAULT_SOURCE_GLOB = "ESCO dataset*json-ld*.zip"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_source(root: Path) -> Path:
    candidates = sorted((root / "data").glob(_DEFAULT_SOURCE_GLOB))
    if not candidates:
        raise FileNotFoundError(
            "ESCO JSON-LD zip not found in data/. Download from "
            "https://esco.ec.europa.eu/en/use-esco/download"
        )
    return candidates[-1]


async def _run_one(conn, system_id: str, mapping: dict, dry_run: bool) -> None:
    before = await conn.fetchval(
        "SELECT COUNT(*) FROM classification_node "
        "WHERE system_id = $1 AND (description IS NULL OR description = '')",
        system_id,
    )
    print(f"  [{system_id}] before: {before:,} empty rows")
    if dry_run:
        rows = await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = $1 AND (description IS NULL OR description = '')",
            system_id,
        )
        would = sum(1 for r in rows if r["code"] in mapping)
        print(f"  [{system_id}] dry run: would update {would:,} rows")
        return
    updated = await apply_descriptions(conn, system_id, mapping)
    after = await conn.fetchval(
        "SELECT COUNT(*) FROM classification_node "
        "WHERE system_id = $1 AND (description IS NULL OR description = '')",
        system_id,
    )
    print(f"  [{system_id}] updated {updated:,} rows, {after:,} still empty")


async def _run(args: argparse.Namespace) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _find_source(root)
    print(f"  source: {source.name}")

    targets = list(_TARGETS.items()) if args.only == "all" else [
        (args.only, _TARGETS[args.only])
    ]

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        for label, (system_id, concept_type) in targets:
            print(f"  Parsing ESCO {label}...")
            mapping = parse_esco_descriptions(source, concept_type=concept_type)
            print(f"  Parsed {len(mapping):,} English descriptions for {label}")
            await _run_one(conn, system_id, mapping, dry_run=args.dry_run)
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only",
        choices=["all", "occupations", "skills"],
        default="all",
    )
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
