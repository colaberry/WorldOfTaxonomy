"""Backfill ONET content-model taxonomy descriptions by title match.

Populates description for every row in the six ONET content-model
systems (``onet_knowledge``, ``onet_abilities``, ``onet_interests``,
``onet_work_activities``, ``onet_work_context``, ``onet_work_styles``)
whose title matches an Element Name in the ONET Content Model
Reference file. DB codes like ``ONA.01`` are local aliases, but the
titles match ONET's ``Element Name`` 1:1.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.onet_content_model import (
    normalize_title,
    parse_content_model_reference,
)


_CM_FILE = Path("data/onet_db/db_29_3_text/Content Model Reference.txt")
_TARGET_SYSTEMS: List[str] = [
    "onet_knowledge",
    "onet_abilities",
    "onet_interests",
    "onet_work_activities",
    "onet_work_context",
    "onet_work_styles",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    cm_path = root / _CM_FILE
    if not cm_path.exists():
        print(f"ERROR: {cm_path} not found", file=sys.stderr)
        return 1

    title_to_desc = parse_content_model_reference(cm_path)
    print(f"  Loaded {len(title_to_desc):,} ONET content-model descriptions")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        total_updated = 0
        for sid in _TARGET_SYSTEMS:
            empty_rows = await conn.fetch(
                "SELECT code, title FROM classification_node "
                "WHERE system_id = $1 "
                "AND (description IS NULL OR description = '')",
                sid,
            )
            mapping: Dict[str, str] = {}
            for r in empty_rows:
                desc = title_to_desc.get(normalize_title(r["title"]))
                if desc:
                    mapping[r["code"]] = desc

            if dry_run:
                print(f"    {sid:25s} empty={len(empty_rows):>3} would-update={len(mapping):>3}")
                total_updated += len(mapping)
                continue

            updated = await apply_descriptions(conn, sid, mapping)
            after = await conn.fetchval(
                "SELECT COUNT(*) FROM classification_node "
                "WHERE system_id = $1 AND (description IS NULL OR description = '')",
                sid,
            )
            print(f"    {sid:25s} updated={updated:>3} still-empty={after:>3}")
            total_updated += updated
        print(f"  Total updated: {total_updated:,}")
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
