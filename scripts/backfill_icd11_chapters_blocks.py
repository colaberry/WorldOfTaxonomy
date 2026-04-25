"""Fetch ICD-11 chapter and block descriptions via WHO API.

The Simple Tabulation TSV (used by PR #44 / #45) lists only the
codes that can appear on a death-certificate or claim form. The
chapter codes (``CH01``..``CH26``, ``CHV``, ``CHX``) and the
block-level container codes (``BlockL1-*``, ``BlockL2-*``) are not
in that TSV but are reachable through the WHO API. This script
walks the linearization tree from the MMS root, fetches each
container entity, and applies the resulting descriptions to the
``icd_11`` system.

Auth: same OAuth2 client-credentials flow as
``backfill_icd11_api_descriptions.py``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import asyncpg
import httpx
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.icd11_api import (
    ICD11_API_HEADERS,
    ICD11_TOKEN_URL,
    render_entity,
    rewrite_release,
)

_SYSTEM_ID = "icd_11"
_DEFAULT_RELEASE = "2026-01"
_MMS_ROOT = "https://id.who.int/icd/release/11/2026-01/mms"
_CACHE = Path("data/.icd11_chapters_cache.jsonl")
_CONCURRENCY = 6


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _db_code_from_entity(entity: dict) -> Optional[str]:
    """Map a WHO API entity to our DB code.

    Chapters: ``code = '01'`` -> ``CH01``; specials ``CHV`` / ``CHX``
    use ``classKind`` and titles to disambiguate. Blocks keep their
    URI suffix encoded into the BlockL{N}-{tail} format that the
    structural ingester used.
    """
    kind = entity.get("classKind") or ""
    code = entity.get("code") or ""
    uri = entity.get("@id") or ""
    if kind == "chapter":
        if not code:
            # Special chapters - V (functioning assessment) and X
            # (extension codes) - identified by URI tail in the API.
            tail = uri.rstrip("/").rsplit("/", 1)[-1]
            if tail.isdigit():
                return None
            return None  # leave to caller
        # Numeric chapter code padded to 2 digits with CH prefix
        if code.isdigit():
            return f"CH{int(code):02d}"
        # Letter chapters like 'V' or 'X'
        return f"CH{code.upper()}"
    if kind == "block":
        # Construct BlockL{depth}-{stem} key from URI. Blocks live at
        # /mms/<uri-path> where the uri-path encodes the level.
        # The DB code format is BlockL1-1A0 etc.; we cannot reconstruct
        # that without round-tripping. Return None and let the caller
        # match by title.
        return None
    return None


class _TokenManager:
    def __init__(self, client_id: str, client_secret: str):
        self._cid = client_id
        self._sec = client_secret
        self._token = ""
        self._expires_at = 0.0

    async def get(self, client: httpx.AsyncClient, *, force: bool = False) -> str:
        if not force and self._token and time.time() < self._expires_at - 60:
            return self._token
        r = await client.post(
            ICD11_TOKEN_URL,
            data={
                "client_id": self._cid,
                "client_secret": self._sec,
                "scope": "icdapi_access",
                "grant_type": "client_credentials",
            },
        )
        r.raise_for_status()
        body = r.json()
        self._token = body["access_token"]
        self._expires_at = time.time() + int(body.get("expires_in", 3600))
        return self._token


async def _fetch(client: httpx.AsyncClient, token_mgr: _TokenManager, uri: str) -> Optional[dict]:
    # WHO returns API URIs in http:// form but redirects to https.
    # httpx does not follow redirects by default; rewrite up front.
    if uri.startswith("http://id.who.int/"):
        uri = "https://" + uri[len("http://"):]
    token = await token_mgr.get(client)
    headers = {**ICD11_API_HEADERS, "Authorization": f"Bearer {token}"}
    for attempt in range(3):
        r = await client.get(uri, headers=headers, timeout=30.0)
        if r.status_code == 401:
            token = await token_mgr.get(client, force=True)
            headers["Authorization"] = f"Bearer {token}"
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 502, 503, 504):
            await asyncio.sleep(1.0 + attempt)
            continue
        return None
    return None


async def _walk_tree(
    client: httpx.AsyncClient,
    token_mgr: _TokenManager,
    root_uri: str,
    *,
    title_to_db_code: Dict[str, str],
    max_depth: int = 3,
) -> Dict[str, str]:
    """Walk the chapter/block tree breadth-first, return
    ``{db_code: description}`` for every chapter and block entity
    whose title matches a DB row title with empty description.

    Containers (chapter, block) only -- skip leaf categories the
    Simple Tabulation script already covered.
    """
    out: Dict[str, str] = {}
    queue: List[tuple[str, int]] = [(root_uri, 0)]
    seen: set = set()

    visited_chapters = 0
    visited_blocks = 0
    matched = 0

    while queue:
        uri, depth = queue.pop(0)
        if uri in seen:
            continue
        seen.add(uri)
        if depth > max_depth:
            continue
        entity = await _fetch(client, token_mgr, uri)
        if not entity:
            continue
        kind = entity.get("classKind", "")
        if kind == "chapter":
            visited_chapters += 1
        elif kind == "block":
            visited_blocks += 1
        if kind in ("chapter", "block"):
            title = entity.get("title", "")
            if isinstance(title, dict):
                title = title.get("@value", "")
            db_code = title_to_db_code.get(title.strip())
            if db_code:
                rendered = render_entity(entity)
                if rendered:
                    out[db_code] = rendered
                    matched += 1
        # Recurse into children
        for child_uri in entity.get("child", []):
            queue.append((child_uri, depth + 1))

    print(f"  walk: visited_chapters={visited_chapters} visited_blocks={visited_blocks} matched={matched}")
    return out


async def _run(dry_run: bool, max_depth: int) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    cid = os.environ.get("WHO_ICD11_CLIENT_ID")
    sec = os.environ.get("WHO_ICD11_CLIENT_SECRET")
    if not (database_url and cid and sec):
        print("ERROR: missing DATABASE_URL or WHO_ICD11_* env vars", file=sys.stderr)
        return 1

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        rows = await conn.fetch(
            "SELECT code, title FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '') "
            "AND (code LIKE 'CH%' OR code LIKE 'BlockL%')"
        )
        title_to_code = {(r["title"] or "").strip(): r["code"] for r in rows}
        print(f"  Empty container rows (CH* or BlockL*): {len(title_to_code):,}")

        if not title_to_code:
            return 0

        token_mgr = _TokenManager(cid, sec)
        async with httpx.AsyncClient(http2=False) as client:
            mapping = await _walk_tree(
                client, token_mgr, _MMS_ROOT,
                title_to_db_code=title_to_code,
                max_depth=max_depth,
            )
        print(f"  Resolved {len(mapping):,} container descriptions")

        if dry_run:
            for k in list(mapping)[:5]:
                print(f"    {k} -> {mapping[k][:80]}")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Updated {updated:,}; still empty {after:,}")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--max-depth", type=int, default=3,
        help="Max tree-walk depth (1=chapters only, 2=+L1 blocks, 3=+L2 blocks)",
    )
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run, max_depth=args.max_depth))


if __name__ == "__main__":
    sys.exit(main())
