"""Backfill ISO 3166-1 country descriptions from ``data/iso3166_all.csv``.

The on-disk CSV pairs alpha-2, alpha-3, M.49 numeric, and UN region /
sub-region for every country. The DB system ``iso_3166_1`` stores
alpha-2 codes; we render the same "X is a country in <sub_region>,
<region>. ISO alpha-3 code: XYZ." sentence used by the ISO 3166-2
backfill (#52) and the UN M.49 backfill (#62).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from pathlib import Path
from typing import Dict

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions

_SOURCE = Path("data/iso3166_all.csv")
_SYSTEM_ID = "iso_3166_1"
_EM_DASH = "\u2014"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _render(meta: Dict[str, str]) -> str:
    name = (meta.get("name") or "").strip()
    alpha3 = (meta.get("alpha3") or "").strip()
    region = (meta.get("region") or "").strip()
    sub = (meta.get("sub_region") or "").strip()
    parts = []
    if sub:
        parts.append(sub)
    if region and region != sub:
        parts.append(region)
    location = ", ".join(parts)
    if location:
        lead = f"{name} is a country in {location}."
    else:
        lead = f"{name}."
    if alpha3:
        lead = f"{lead} ISO alpha-3 code: {alpha3}."
    return lead.replace(_EM_DASH, "-")


def _build_mapping(csv_path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    with Path(csv_path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            alpha2 = (row.get("alpha-2") or "").strip()
            if not alpha2:
                continue
            out[alpha2] = _render({
                "name": row.get("name", ""),
                "alpha3": row.get("alpha-3", ""),
                "region": row.get("region", ""),
                "sub_region": row.get("sub-region", ""),
            })
    return out


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    src = root / _SOURCE
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        return 1

    mapping = _build_mapping(src)
    print(f"  Built {len(mapping):,} country descriptions")

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
                "AND (description IS NULL OR description = '')"
            )
            would = sum(1 for r in rows if r["code"] in mapping)
            print(f"  Dry run: would update {would:,} from CSV")
            return 0
        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        print(f"  Applied from CSV: {updated:,}")

        # Cascade UN M.49 region descriptions for the 22 numeric codes
        # that iso_3166_1 carries alongside alpha-2 country codes.
        m49_rows = await conn.fetch(
            "SELECT code, description FROM classification_node "
            "WHERE system_id = 'un_m49' "
            "AND description IS NOT NULL AND description <> ''"
        )
        m49_map = {r["code"]: r["description"] for r in m49_rows}
        m49_applied = await apply_descriptions(conn, _SYSTEM_ID, m49_map)
        print(f"  Cascaded from un_m49: {m49_applied:,}")

        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        total_updated = updated + m49_applied
        print(f"  Total updated: {total_updated:,}; still-empty {after:,}")
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
