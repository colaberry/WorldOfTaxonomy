"""Backfill SIC 1987 descriptions by scraping OSHA's per-code HTML pages.

Each SIC code is served at ``https://www.osha.gov/sic-manual/<code>``.
Pages are cached under ``data/sic/pages/<code>.html`` so re-runs skip
network I/O. Uses httpx.AsyncClient with bounded concurrency.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
import httpx
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.sic1987_descriptions import extract_description


_CACHE = Path("data/sic/pages")
_SYSTEM_ID = "sic_1987"
_BASE_URL = "https://www.osha.gov/sic-manual/"
_HEADERS = {"User-Agent": "Mozilla/5.0 WorldOfTaxonomy-backfill"}
_CONCURRENCY = 10
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


async def _fetch_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    code: str,
    cache: Path,
) -> bytes:
    path = cache / f"{code}.html"
    if path.exists() and path.stat().st_size > 5000:
        return path.read_bytes()
    url = _BASE_URL + code
    async with sem:
        for attempt in range(4):
            try:
                r = await client.get(url, headers=_HEADERS, timeout=_TIMEOUT)
                if r.status_code == 200 and r.content:
                    path.write_bytes(r.content)
                    return r.content
                if r.status_code == 404:
                    # Cache 404 as empty sentinel so we don't retry
                    path.write_bytes(b"")
                    return b""
                await asyncio.sleep(1.0 + attempt)
            except httpx.HTTPError:
                await asyncio.sleep(1.0 + attempt)
        return b""


async def _run(dry_run: bool, limit: int) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    cache = root / _CACHE
    cache.mkdir(parents=True, exist_ok=True)

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        rows = await conn.fetch(
            "SELECT code, title FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
            " ORDER BY code"
        )
        if limit:
            rows = rows[:limit]
        print(f"  SIC codes to fetch: {len(rows):,}")

        mapping: dict[str, str] = {}
        sem = asyncio.Semaphore(_CONCURRENCY)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [
                asyncio.create_task(
                    _fetch_one(client, sem, r["code"], cache)
                )
                for r in rows
            ]
            for i, r in enumerate(rows, 1):
                page = await tasks[i - 1]
                if not page:
                    continue
                desc = extract_description(
                    page.decode("utf-8", errors="replace"),
                    code=r["code"],
                    title=r["title"],
                )
                if desc:
                    mapping[r["code"]] = desc
                if i % 100 == 0:
                    print(f"    fetched {i:,}/{len(rows):,}  (mapped {len(mapping):,})")

        print(f"  Extracted descriptions: {len(mapping):,}")

        if dry_run:
            print(f"  Dry run: would update {len(mapping):,} rows")
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
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    sys.exit(main())
