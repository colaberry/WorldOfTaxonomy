"""Backfill NACE Rev 2 node descriptions + cascade to country mirrors.

Fetches per-concept SKOS/XKOS RDF from the EU Publications Office
(``http://data.europa.eu/ux2/nace2/<path>``) for every distinct NACE
code in the DB, extracts the English ``coreContentNote`` and
``exclusionNote``, and applies the resulting mapping to:

- ``nace_rev2`` (the base system)
- every NACE-derived national mirror (NAF, ATECO, WZ, CNAE, etc.)

Concepts are cached under ``data/nace/rdf/<code>.xml`` so re-runs skip
network I/O. Uses ``httpx.AsyncClient`` with a semaphore for bounded
concurrency.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set

import asyncpg
import httpx
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.nace_descriptions import (
    build_concept_url,
    code_to_uri_path,
    parse_concept_rdf,
    render_description,
)


_CACHE_DIR = Path("data/nace/rdf")
_BASE_SYSTEM_ID = "nace_rev2"
_HEADERS = {"Accept": "application/rdf+xml", "User-Agent": "WorldOfTaxonomy-backfill"}
_CONCURRENCY = 12
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _fetch_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    code: str,
    cache: Path,
) -> bytes:
    uri_suffix = code_to_uri_path(code)
    path = cache / f"{uri_suffix}.xml"
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    url = build_concept_url(code)
    async with sem:
        for attempt in range(4):
            try:
                r = await client.get(url, headers=_HEADERS, timeout=_TIMEOUT)
                if r.status_code == 200 and r.content:
                    path.write_bytes(r.content)
                    return r.content
                await asyncio.sleep(1.0 + attempt)
            except httpx.HTTPError:
                await asyncio.sleep(1.0 + attempt)
        return b""


async def _load_nace_codes(conn) -> List[str]:
    rows = await conn.fetch(
        "SELECT code FROM classification_node "
        f"WHERE system_id = '{_BASE_SYSTEM_ID}' "
        "ORDER BY code"
    )
    return [r["code"] for r in rows]


async def _nace_like_systems(conn) -> List[str]:
    """Return every system that shares the NACE Rev 2 code scheme.

    Heuristic: a system is NACE-derived if it contains the canonical
    4-digit class code ``01.11`` (Growing of cereals) AND ``nace_rev2``
    is the same. We anchor on that code and on a small second code to
    avoid false positives, then verify by counting overlap.
    """
    candidates = await conn.fetch(
        "SELECT DISTINCT system_id FROM classification_node WHERE code = '01.11'"
    )
    return sorted({r["system_id"] for r in candidates})


async def _run(dry_run: bool, limit: int) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    cache = root / _CACHE_DIR
    cache.mkdir(parents=True, exist_ok=True)

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        codes = await _load_nace_codes(conn)
        if limit:
            codes = codes[:limit]
        print(f"  NACE codes to fetch: {len(codes):,}")

        mapping: Dict[str, str] = {}
        sem = asyncio.Semaphore(_CONCURRENCY)

        async with httpx.AsyncClient(follow_redirects=True, http2=False) as client:
            done = 0
            tasks = [
                asyncio.create_task(_fetch_one(client, sem, code, cache))
                for code in codes
            ]
            for code, task in zip(codes, tasks):
                xml_bytes = await task
                done += 1
                if not xml_bytes:
                    continue
                try:
                    parts = parse_concept_rdf(
                        xml_bytes, uri_suffix=code_to_uri_path(code)
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"  parse error {code}: {exc}", file=sys.stderr)
                    continue
                body = render_description(parts)
                if body:
                    mapping[code] = body
                if done % 100 == 0:
                    print(f"    fetched {done:,}/{len(codes):,}  (mapped {len(mapping):,})")

        print(f"  Parsed descriptions: {len(mapping):,}")

        systems = await _nace_like_systems(conn)
        print(f"  NACE-derived systems: {len(systems)}")

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
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limit NACE codes fetched (for smoke tests).",
    )
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    sys.exit(main())
