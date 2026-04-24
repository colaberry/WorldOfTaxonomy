"""Backfill ISCED-F 2013 node descriptions from the ESCO JSON-LD file."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import zipfile
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.iscedf2013_from_esco import (
    parse_iscedf2013_descriptions,
)


_SOURCE_ZIP = Path("data/ESCO dataset - v1.2.1 - classification -  - json-ld.zip")
_EXTRACTED = Path("data/esco-v1.2.1.json-ld")
_SYSTEM_ID = "iscedf_2013"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_extracted(root: Path) -> Path:
    extracted = root / _EXTRACTED
    if extracted.exists() and extracted.stat().st_size > 0:
        return extracted
    zip_path = root / _SOURCE_ZIP
    if not zip_path.exists():
        print(f"ERROR: {zip_path} not found", file=sys.stderr)
        sys.exit(1)
    print(f"  Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path) as z:
        name = next((n for n in z.namelist() if n.lower().endswith(".json-ld")), None)
        if name is None:
            print("ERROR: no .json-ld inside ESCO archive", file=sys.stderr)
            sys.exit(1)
        with z.open(name) as src, extracted.open("wb") as dst:
            while chunk := src.read(1 << 20):
                dst.write(chunk)
    return extracted


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    jsonld = _ensure_extracted(root)
    print(f"  Streaming {jsonld.name}...")
    mapping = parse_iscedf2013_descriptions(jsonld)
    print(f"  Parsed {len(mapping):,} ISCED-F descriptions")

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
