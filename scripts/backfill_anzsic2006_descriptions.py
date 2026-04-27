"""Backfill ANZSIC 2006 node descriptions from the ABS SDMX codelist."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import urllib.request
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.anzsic2006_descriptions import (
    parse_anzsic2006_descriptions,
)
from world_of_taxonomy.ingest.descriptions import apply_descriptions


_SOURCE_URL = (
    "https://api.data.abs.gov.au/codelist/ABS/CL_ANZSIC_2006/1.0.0"
)
_SOURCE_PATH = Path("data/anzsic_2006.xml")
_SYSTEM_ID = "anzsic_2006"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_downloaded(root: Path) -> Path:
    local = root / _SOURCE_PATH
    if local.exists() and local.stat().st_size > 1_000_000:
        return local
    print(f"  Downloading {_SOURCE_URL}...")
    req = urllib.request.Request(
        _SOURCE_URL,
        headers={"Accept": "application/vnd.sdmx.structure+xml"},
    )
    with urllib.request.urlopen(req) as resp, local.open("wb") as dst:
        while chunk := resp.read(1 << 20):
            dst.write(chunk)
    print(f"  Saved to {local} ({local.stat().st_size:,} bytes)")
    return local


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    source = _ensure_downloaded(root)
    print(f"  Parsing {source.name}...")
    mapping = parse_anzsic2006_descriptions(source)
    print(f"  Parsed {len(mapping):,} CONTEXT descriptions")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Before: {before:,} empty rows")

        if dry_run:
            rows = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' "
                "  AND (description IS NULL OR description = '')"
            )
            would = sum(1 for r in rows if r["code"] in mapping)
            print(f"  Dry run: would update {would:,} rows")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Updated {updated:,} rows, {after:,} still empty")
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
