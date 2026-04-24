"""Backfill ISIC Rev 4 node descriptions + cascade to country mirrors.

Builds a crosswalk-correct mapping from the NACE Rev 2 RDF cache
(populated by ``scripts/backfill_nace_descriptions.py``) using
``data/crosswalk/ISIC4_to_NACE2.txt`` to translate ISIC codes to their
corresponding NACE codes. Only 1:1 exact matches (``ISIC4part == 0``
and ``NACE2part == 0``, single NACE partner) are kept so that no
mislabelled notes are applied -- NACE often renumbers ISIC classes
when subdividing (e.g. ISIC ``4661`` -> NACE ``46.71``, distinct from
NACE ``46.61``).

Applies the resulting ``{isic_code: markdown}`` mapping to every
ISIC-derived system discovered in the DB (detected by membership of
the canonical 4-digit class ``0111`` "Growing of cereals").
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

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.isic_cascade_from_nace import (
    build_isic_mapping,
)


_CACHE_DIR = Path("data/nace/rdf")
_CROSSWALK = Path("data/crosswalk/ISIC4_to_NACE2.txt")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _isic_like_systems(conn) -> List[str]:
    """Return every system whose code scheme *is* ISIC Rev 4.

    A bare "has code 0111" test is not enough: ANZSIC, US SIC 1987,
    UN CPC v2.1 and ISCED-F 2013 all happen to contain the 4-digit
    code ``0111`` but use completely different numbering conventions
    downstream. We require the candidate system to share at least 95%
    of its code set with ``isic_rev4`` -- the true ISIC mirrors
    (isic_*, ciiu_*, kbli_id, bsic, caeb, nic_2008, psic_pk, slsic,
    vsic_2018) are all at 100%.
    """
    isic_codes = await conn.fetch(
        "SELECT code FROM classification_node WHERE system_id = 'isic_rev4'"
    )
    isic_set = {r["code"] for r in isic_codes}
    rows = await conn.fetch(
        "SELECT DISTINCT system_id FROM classification_node "
        "WHERE code = '0111' AND system_id <> 'isic_rev4' ORDER BY system_id"
    )
    selected: List[str] = ["isic_rev4"]
    for r in rows:
        sid = r["system_id"]
        codes = await conn.fetch(
            "SELECT code FROM classification_node WHERE system_id = $1", sid
        )
        system_codes = {x["code"] for x in codes}
        overlap = len(isic_set & system_codes)
        if len(system_codes) > 0 and overlap / len(isic_set) >= 0.95:
            selected.append(sid)
    return sorted(selected)


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    cache = root / _CACHE_DIR
    crosswalk = root / _CROSSWALK
    if not cache.exists():
        print(
            f"ERROR: NACE RDF cache not found at {cache}. "
            "Run scripts/backfill_nace_descriptions.py first.",
            file=sys.stderr,
        )
        return 1
    if not crosswalk.exists():
        print(
            f"ERROR: ISIC4 <-> NACE2 crosswalk not found at {crosswalk}.",
            file=sys.stderr,
        )
        return 1

    print(f"  Reading cache:     {cache}")
    print(f"  Reading crosswalk: {crosswalk}")
    mapping = build_isic_mapping(cache_dir=cache, crosswalk_path=crosswalk)
    print(f"  Built ISIC->note mapping: {len(mapping):,} entries (1:1 exact matches only)")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        systems = await _isic_like_systems(conn)
        print(f"  ISIC-derived systems: {len(systems)}")

        if dry_run:
            for sid in systems:
                empty = await conn.fetchval(
                    "SELECT COUNT(*) FROM classification_node "
                    "WHERE system_id = $1 AND (description IS NULL OR description='')",
                    sid,
                )
                would = await conn.fetchval(
                    "SELECT COUNT(*) FROM classification_node "
                    "WHERE system_id = $1 "
                    "AND (description IS NULL OR description='') "
                    "AND code = ANY($2::text[])",
                    sid,
                    list(mapping.keys()),
                )
                print(f"    {sid:20s} empty={empty:>5,} would-update={would:>5,}")
            return 0

        total_updated = 0
        for sid in systems:
            updated = await apply_descriptions(conn, sid, mapping)
            after = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                "WHERE system_id = $1 AND (description IS NULL OR description='')",
                sid,
            )
            total_updated += updated
            print(f"    {sid:20s} updated={updated:>5,} still-empty={after:>5,}")
        print(f"  Total updated across systems: {total_updated:,}")
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
