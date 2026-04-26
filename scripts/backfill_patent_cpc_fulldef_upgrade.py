"""Upgrade patent_cpc descriptions where FullCPCDefinitionXML
content is significantly richer than what the existing description
holds.

Policy ("upgrade-on-richness"):

- Skip if no existing description (the original NULL-only PR #76
  already wrote those rows).
- Skip if the new content is shorter or only marginally longer than
  the existing.
- **Upgrade** when:
  - The new content is at least 1.5x the length of the existing,
    AND
  - The new content contains at least one structured section
    header that the existing lacks (one of "**Definition:**",
    "**Limiting references", "**Application-oriented references:**",
    "**Glossary:**").

This is the only PR in the description-backfill series that
overwrites populated description rows. It is gated behind a
``--apply`` flag so a dry run is the default; live application
requires explicit user confirmation.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.patent_cpc_full_definition import (
    parse_definition_zip,
)


_SOURCE = Path("data/FullCPCDefinitionXML202601.zip")
_SYSTEM_ID = "patent_cpc"
_LENGTH_RATIO = 1.5
_SECTION_HEADERS = (
    "**Definition:**",
    "**Limiting references",
    "**Application-oriented references:**",
    "**Glossary:**",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_richer(new: str, existing: str) -> bool:
    """Return True when ``new`` is significantly richer than ``existing``."""
    if not new or not existing:
        return False
    if len(new) < len(existing) * _LENGTH_RATIO:
        return False
    new_sections = {h for h in _SECTION_HEADERS if h in new}
    old_sections = {h for h in _SECTION_HEADERS if h in existing}
    return bool(new_sections - old_sections)


async def _run(*, apply: bool) -> int:
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

    print(f"  Parsing {src.name}...")
    mapping = parse_definition_zip(src)
    print(f"  FullDef extracted {len(mapping):,} CPC items")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        existing_rows = await conn.fetch(
            "SELECT code, description FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND description IS NOT NULL AND description <> ''"
        )
        existing_map = {r["code"]: r["description"] for r in existing_rows}
        print(f"  Existing populated rows: {len(existing_map):,}")

        upgrades: list[tuple[str, str, str]] = []
        for code, new_body in mapping.items():
            existing = existing_map.get(code)
            if not existing:
                continue
            if _is_richer(new_body, existing):
                upgrades.append((code, existing, new_body))
        print(f"  Upgrade candidates: {len(upgrades):,}")

        if not apply:
            print("\n  [DRY RUN] sample of 5 upgrades:")
            for code, old, new in upgrades[:5]:
                print(f"    {code}: {len(old)} -> {len(new)} chars")
            print("\n  Re-run with --apply to write the upgrades.")
            return 0

        print(f"\n  Applying {len(upgrades):,} upgrades...")
        async with conn.transaction():
            for code, _old, new in upgrades:
                await conn.execute(
                    "UPDATE classification_node "
                    "SET description = $2 "
                    f"WHERE system_id = '{_SYSTEM_ID}' AND code = $1",
                    code, new,
                )
        print(f"  Updated {len(upgrades):,} rows")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually write the upgrades. Without this flag, dry run only.",
    )
    args = parser.parse_args()
    return asyncio.run(_run(apply=args.apply))


if __name__ == "__main__":
    sys.exit(main())
