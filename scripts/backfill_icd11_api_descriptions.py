"""Backfill ICD-11 descriptions from the authenticated WHO ICD-11 API.

The Simple Tabulation file (used by PR #44) carries only the
``CodingNote`` column -- roughly 1.6% coverage. The full
Definition / Long definition / Inclusion / Exclusion blocks live only
behind the authenticated API, so this script fetches one entity per
code and replaces the thinner description with the richer one.

Design notes:

* Code -> Linearization URI is read from the Simple Tabulation TSV we
  already have on disk. That avoids a second round-trip to
  ``/codeinfo/`` per code.
* Fetches run concurrently (``--concurrency``, default 10). WHO does
  not publish a hard rate limit; 10 is well within their observed
  comfort and lets us finish ~37K codes in under an hour.
* A checkpoint file (``data/.icd11_api_cache.jsonl``) records every
  fetched render (including empty renders) so re-runs skip work.
* Tokens last 3600s; we refresh automatically on 401.
* The final DB write is an idempotent overwrite: the API block is
  strictly richer than anything PR #44 could have written, so we do
  not preserve the older CodingNote-only rows.

Usage:
    python -m scripts.backfill_icd11_api_descriptions --limit 50 --dry-run
    python -m scripts.backfill_icd11_api_descriptions --dry-run
    python -m scripts.backfill_icd11_api_descriptions
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict

import asyncpg
import httpx
from dotenv import load_dotenv

from world_of_taxonomy.ingest.icd11_api import (
    ICD11_API_HEADERS,
    ICD11_TOKEN_URL,
    parse_code_to_uri_map,
    render_entity,
    rewrite_release,
)

_SYSTEM_ID = "icd_11"
_CHECKPOINT = Path("data/.icd11_api_cache.jsonl")
_SOURCE_GLOB = "SimpleTabulation-ICD-11-MMS*.zip"
_DEFAULT_RELEASE = "2026-01"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _find_source(root: Path) -> Path:
    candidates = sorted((root / "data").glob(_SOURCE_GLOB))
    if not candidates:
        raise FileNotFoundError(
            "Simple Tabulation ZIP not found under data/. Download from "
            "https://icd.who.int/browse/latestrelease/mms/en"
        )
    return candidates[-1]


class _TokenManager:
    """Tiny OAuth2 client-credentials holder with auto-refresh on 401."""

    def __init__(self, client_id: str, client_secret: str):
        self._cid = client_id
        self._sec = client_secret
        self._token = ""
        self._expires_at = 0.0

    async def get(self, client: httpx.AsyncClient, *, force: bool = False) -> str:
        if not force and self._token and time.time() < self._expires_at - 60:
            return self._token
        resp = await client.post(
            ICD11_TOKEN_URL,
            data={
                "client_id": self._cid,
                "client_secret": self._sec,
                "scope": "icdapi_access",
                "grant_type": "client_credentials",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        self._token = body["access_token"]
        self._expires_at = time.time() + int(body.get("expires_in", 3600))
        return self._token


async def _fetch_one(
    client: httpx.AsyncClient,
    tokens: _TokenManager,
    uri: str,
    *,
    max_retries: int = 5,
) -> dict | None:
    delay = 1.0
    for attempt in range(max_retries):
        tok = await tokens.get(client)
        headers = dict(ICD11_API_HEADERS)
        headers["Authorization"] = f"Bearer {tok}"
        try:
            resp = await client.get(uri, headers=headers)
        except httpx.RequestError:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)
            continue
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 401:
            await tokens.get(client, force=True)
            continue
        if resp.status_code == 404:
            return None
        if resp.status_code in (429, 500, 502, 503, 504):
            await asyncio.sleep(delay)
            delay = min(delay * 2, 30)
            continue
        return None
    return None


def _load_checkpoint(path: Path) -> Dict[str, str | None]:
    if not path.exists():
        return {}
    out: Dict[str, str | None] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[rec["code"]] = rec.get("description")
    return out


def _append_checkpoint(path: Path, code: str, description: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"code": code, "description": description}) + "\n")


async def _fetch_all(
    code_to_uri: Dict[str, str],
    cache: Dict[str, str | None],
    client_id: str,
    client_secret: str,
    concurrency: int,
    limit: int | None,
    log_every: int,
    release: str,
) -> Dict[str, str | None]:
    todo = [
        (code, uri) for code, uri in code_to_uri.items() if code not in cache
    ]
    todo.sort(key=lambda t: t[0])
    if limit is not None:
        todo = todo[:limit]
    print(f"  Fetching {len(todo):,} new entities (cache has {len(cache):,} already)")

    if not todo:
        return cache

    tokens = _TokenManager(client_id, client_secret)
    sem = asyncio.Semaphore(concurrency)
    done = 0
    done_lock = asyncio.Lock()
    t0 = time.time()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        await tokens.get(client)

        async def _one(code: str, uri: str):
            nonlocal done
            dated = rewrite_release(uri, release)
            async with sem:
                entity = await _fetch_one(client, tokens, dated)
            description = render_entity(entity) if entity else ""
            value = description if description else None
            cache[code] = value
            _append_checkpoint(_CHECKPOINT, code, value)
            async with done_lock:
                done += 1
                if done % log_every == 0:
                    elapsed = time.time() - t0
                    rate = done / elapsed if elapsed else 0
                    remaining = (len(todo) - done) / rate if rate else 0
                    print(
                        f"    {done:,}/{len(todo):,} "
                        f"({rate:.1f}/s, eta {remaining/60:.1f}m)"
                    )

        await asyncio.gather(*(_one(code, uri) for code, uri in todo))

    elapsed = time.time() - t0
    print(f"  Fetched {len(todo):,} entities in {elapsed/60:.1f}m")
    return cache


async def _apply_to_db(
    url: str, cache: Dict[str, str | None], dry_run: bool
) -> int:
    to_apply = {k: v for k, v in cache.items() if v}
    print(f"  {len(to_apply):,} entities have a non-empty description to apply")
    if dry_run:
        conn = await asyncpg.connect(url, statement_cache_size=0)
        try:
            rows = await conn.fetch(
                "SELECT code FROM classification_node WHERE system_id=$1",
                _SYSTEM_ID,
            )
            existing = {r["code"] for r in rows}
            hits = sum(1 for c in to_apply if c in existing)
            print(f"  Dry run: would overwrite {hits:,} rows in classification_node")
            return 0
        finally:
            await conn.close()

    conn = await asyncpg.connect(url, statement_cache_size=0)
    updated = 0
    try:
        async with conn.transaction():
            for code, desc in to_apply.items():
                result = await conn.execute(
                    """
                    UPDATE classification_node
                       SET description = $3
                     WHERE system_id = $1
                       AND code = $2
                    """,
                    _SYSTEM_ID,
                    code,
                    desc,
                )
                updated += int(result.split()[-1])
    finally:
        await conn.close()
    print(f"  Updated {updated:,} rows")
    return updated


async def _run(args: argparse.Namespace) -> int:
    root = _project_root()
    load_dotenv(root / ".env")

    database_url = os.environ.get("DATABASE_URL")
    client_id = os.environ.get("WHO_ICD11_CLIENT_ID")
    client_secret = os.environ.get("WHO_ICD11_CLIENT_SECRET")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    if not client_id or not client_secret:
        print(
            "ERROR: WHO_ICD11_CLIENT_ID / WHO_ICD11_CLIENT_SECRET not set",
            file=sys.stderr,
        )
        return 1

    source = _find_source(root)
    print(f"  Parsing {source.name}...")
    code_to_uri = parse_code_to_uri_map(source)
    print(f"  {len(code_to_uri):,} codes in Simple Tabulation")

    checkpoint = root / _CHECKPOINT
    cache = _load_checkpoint(checkpoint)

    cache = await _fetch_all(
        code_to_uri,
        cache,
        client_id,
        client_secret,
        concurrency=args.concurrency,
        limit=args.limit,
        log_every=args.log_every,
        release=args.release,
    )

    await _apply_to_db(database_url, cache, dry_run=args.dry_run)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None,
                        help="Only fetch first N uncached codes (for smoke tests)")
    parser.add_argument("--log-every", type=int, default=200)
    parser.add_argument("--release", default=_DEFAULT_RELEASE,
                        help="ICD-11 release date to query (default: %(default)s)")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
