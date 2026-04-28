"""Verified-LLM-synthesis pipeline (Track 2).

For each empty row in a target system:

1. Resolve the parent path via ``parent_code`` (broadest first).
2. Generator (gpt-oss:120b via Ollama) produces a candidate
   description with the parent path injected as context.
3. Verifier (same model, separate prompt) judges the candidate as
   ``yes`` / ``no`` / ``uncertain``.
4. Only ``yes`` rows are written to the DB.
5. ``no`` and ``uncertain`` rows are kept in the cache (with their
   verdict) for human review or re-run at higher temperature.

JSONL cache at ``data/llm_verified/<system_id>.jsonl`` records
every (code, candidate, verdict) triple so re-runs are
deterministic and resumable.

The DB is flushed periodically (default every 500 newly-processed
rows; override via ``FLUSH_EVERY_N_ROWS``) so the public-facing
``classification_node.description`` reflects recent verifications
without waiting for end-of-system. The flush is idempotent and
NULL-only.

Usage:

    python3 -m scripts.backfill_llm_verified --systems unspsc_v24 --limit 100
    python3 -m scripts.backfill_llm_verified --systems unspsc_v24
    FLUSH_EVERY_N_ROWS=200 python3 -m scripts.backfill_llm_verified --systems patent_cpc
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.llm_descriptions import (
    build_messages,
    sanitize_response,
)
from world_of_taxonomy.ingest.llm_verifier import (
    build_verifier_messages,
    parse_verdict,
)
from world_of_taxonomy.llm_client import chat_json


_CACHE_DIR = Path("data/llm_verified")
_DEFAULT_CONCURRENCY = 4
_DEFAULT_FLUSH_EVERY_N_ROWS = 500


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_cache(path: Path) -> Dict[str, Dict[str, str]]:
    """Return ``{code: {candidate, verdict}}`` from the JSONL cache."""
    if not path.exists():
        return {}
    out: Dict[str, Dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            code = rec.get("code")
            if code:
                out[code] = {
                    "candidate": rec.get("candidate", "") or "",
                    "verdict": rec.get("verdict", "") or "",
                }
    return out


def _append_cache(path: Path, code: str, candidate: str, verdict: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "code": code,
            "candidate": candidate,
            "verdict": verdict,
        }) + "\n")


async def _build_parent_path(conn, system_id: str, code: str) -> str:
    """Walk parent_code up to the root and return a multi-line
    'broadest first' string of parent titles.
    """
    titles: List[str] = []
    cursor: Optional[str] = code
    seen: set = set()
    for _ in range(10):  # bound the walk
        if cursor is None or cursor in seen:
            break
        seen.add(cursor)
        row = await conn.fetchrow(
            "SELECT title, parent_code FROM classification_node "
            "WHERE system_id = $1 AND code = $2",
            system_id, cursor,
        )
        if not row:
            break
        if cursor != code and row["title"]:
            titles.append(row["title"])
        cursor = row["parent_code"]
    return "\n".join(reversed(titles))


async def _generate(
    sem: asyncio.Semaphore,
    *,
    system_name: str,
    code: str,
    title: str,
    parent_context: str,
) -> str:
    async with sem:
        for attempt in range(3):
            try:
                raw = await chat_json(
                    build_messages(
                        system_name=system_name,
                        code=code,
                        title=title,
                        parent_context=parent_context,
                    ),
                    # gpt-oss models route chain-of-thought into a hidden
                    # `reasoning` field that consumes tokens before any
                    # visible content is emitted. With 400 tokens, ~6% of
                    # fresh rows finish reasoning with zero visible bytes
                    # and the sanitizer emits an empty candidate.
                    # 1200 gives reasoning room without inflating cost
                    # meaningfully. Verified on patent_cpc bench 2026-04-28.
                    max_tokens=1200,
                    temperature=0.2 if attempt > 0 else 0.0,
                    timeout=60.0,
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"    gen error {code} attempt {attempt+1}: {exc}",
                    file=sys.stderr,
                )
                await asyncio.sleep(1.0 + attempt)
                continue
            sanitized = sanitize_response(raw)
            if sanitized:
                return sanitized
            await asyncio.sleep(0.5 + attempt)
    return ""


async def _verify(
    sem: asyncio.Semaphore,
    *,
    system_name: str,
    code: str,
    title: str,
    candidate: str,
) -> str:
    async with sem:
        for attempt in range(3):
            try:
                raw = await chat_json(
                    build_verifier_messages(
                        system_name=system_name,
                        code=code,
                        title=title,
                        candidate=candidate,
                    ),
                    # Verification is a yes/no/uncertain classification
                    # task; a smaller model can handle it. Override via
                    # VERIFIER_MODEL env var (e.g. "gpt-oss:20b") to
                    # get ~2x throughput by skipping the heavy
                    # 120b reasoning budget on the verifier hop.
                    model=os.environ.get("VERIFIER_MODEL") or None,
                    # gpt-oss:120b consumes a chunk of the budget on
                    # internal reasoning before emitting the verdict;
                    # 20 tokens gets truncated to empty. 200 tokens
                    # gives any model enough room.
                    max_tokens=200,
                    temperature=0.0,
                    timeout=45.0,
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"    verify error {code} attempt {attempt+1}: {exc}",
                    file=sys.stderr,
                )
                await asyncio.sleep(1.0 + attempt)
                continue
            return parse_verdict(raw)
    return "uncertain"


async def _run_one_system(
    pool: "asyncpg.Pool",
    *,
    system_id: str,
    sem: asyncio.Semaphore,
    cache_root: Path,
    limit: int,
    dry_run: bool,
) -> Tuple[int, int, int]:
    async with pool.acquire() as conn:
        sys_meta = await conn.fetchrow(
            "SELECT full_name, name FROM classification_system WHERE id = $1",
            system_id,
        )
        if not sys_meta:
            print(f"  {system_id}: not in DB", file=sys.stderr)
            return (0, 0, 0)
        system_name = sys_meta["full_name"] or sys_meta["name"] or system_id

        rows = await conn.fetch(
            "SELECT code, title FROM classification_node "
            "WHERE system_id = $1 AND (description IS NULL OR description = '') "
            "ORDER BY code",
            system_id,
        )
    if limit:
        rows = rows[:limit]
    if not rows:
        return (0, 0, 0)

    cache_path = cache_root / f"{system_id}.jsonl"
    cached = _load_cache(cache_path)
    print(
        f"  {system_id}: {len(rows):,} empty rows; cached "
        f"{len(cached):,}; to process {len(rows) - len(cached):,}"
    )

    yes_count = no_count = uncertain_count = 0

    # Periodic-flush settings: cache is durable line-by-line (fsync on
    # append), but the DB lags the cache by up to flush_every_n rows.
    # If the process dies mid-system, restart will re-load the cache;
    # however, anyone querying classification_node mid-run sees stale
    # data until the next flush. Periodic apply_descriptions calls
    # close that window.
    flush_every = int(
        os.environ.get("FLUSH_EVERY_N_ROWS")
        or _DEFAULT_FLUSH_EVERY_N_ROWS
    )
    rows_since_last_flush = 0

    async def _flush_yes_to_db() -> int:
        """Apply all current yes-verdicts in cache to the DB. NULL-only;
        idempotent. Returns rows actually updated."""
        if dry_run:
            return 0
        snapshot = _load_cache(cache_path)
        apply_map = {
            c: rec["candidate"]
            for c, rec in snapshot.items()
            if rec["verdict"] == "yes" and rec["candidate"]
        }
        if not apply_map:
            return 0
        async with pool.acquire() as flush_conn:
            return await apply_descriptions(flush_conn, system_id, apply_map)

    # Count cached rows once. Their verdicts are already final.
    pending_rows: List[Dict[str, str]] = []
    for r in rows:
        code = r["code"]
        if code in cached:
            v = cached[code]["verdict"]
            if v == "yes":
                yes_count += 1
            elif v == "no":
                no_count += 1
            else:
                uncertain_count += 1
        else:
            pending_rows.append({"code": code, "title": r["title"] or ""})

    # Concurrent processing: launch up to `concurrency` LLM-call rounds
    # in flight simultaneously. The Semaphore inside _generate / _verify
    # bounds the actual LLM-call concurrency. Without this gather, the
    # for loop above awaited every row serially, making the
    # --concurrency flag a no-op against the loop. Verified by direct
    # measurement 2026-04-28.
    cache_lock = asyncio.Lock()

    async def _process_one(code: str, title: str) -> str:
        async with pool.acquire() as row_conn:
            parent_path = await _build_parent_path(row_conn, system_id, code)
        candidate = await _generate(
            sem,
            system_name=system_name,
            code=code,
            title=title,
            parent_context=parent_path,
        )
        if not candidate:
            async with cache_lock:
                _append_cache(cache_path, code, "", "uncertain")
            return "uncertain"
        verdict = await _verify(
            sem,
            system_name=system_name,
            code=code,
            title=title,
            candidate=candidate,
        )
        async with cache_lock:
            _append_cache(cache_path, code, candidate, verdict)
        return verdict

    # Process in batches sized to the flush interval so the periodic
    # flush + progress log fire at predictable intervals. Within each
    # batch, asyncio.gather + Semaphore enforces the configured
    # concurrency.
    batch_size = max(flush_every, 50)
    for batch_start in range(0, len(pending_rows), batch_size):
        batch = pending_rows[batch_start:batch_start + batch_size]
        verdicts = await asyncio.gather(
            *[_process_one(r["code"], r["title"]) for r in batch]
        )
        for v in verdicts:
            if v == "yes":
                yes_count += 1
            elif v == "no":
                no_count += 1
            else:
                uncertain_count += 1
        rows_since_last_flush += len(batch)
        completed = yes_count + no_count + uncertain_count
        print(
            f"    progress: {completed:,} of {len(rows):,} "
            f"(yes={yes_count:,} no={no_count:,} uncertain={uncertain_count:,})"
        )
        if rows_since_last_flush >= flush_every:
            applied = await _flush_yes_to_db()
            print(
                f"    periodic flush: applied {applied:,} 'yes' rows to DB "
                f"(after {rows_since_last_flush} new rows)"
            )
            rows_since_last_flush = 0

    print(
        f"  {system_id} totals: yes={yes_count:,} no={no_count:,} "
        f"uncertain={uncertain_count:,}"
    )

    if dry_run:
        return (yes_count, no_count, uncertain_count)

    # Apply only YES verdicts
    cached_after = _load_cache(cache_path)
    apply_map = {
        code: rec["candidate"]
        for code, rec in cached_after.items()
        if rec["verdict"] == "yes" and rec["candidate"]
    }
    async with pool.acquire() as apply_conn:
        updated = await apply_descriptions(apply_conn, system_id, apply_map)
    print(f"    applied {updated:,} 'yes' rows to DB")
    return (yes_count, no_count, uncertain_count)


async def _run(
    *, systems: List[str], limit: int, dry_run: bool, concurrency: int,
    cache_dir: Optional[str] = None,
) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    if not (
        os.environ.get("OLLAMA_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    ):
        print("ERROR: no LLM provider configured", file=sys.stderr)
        return 1

    if cache_dir:
        cache_root = Path(cache_dir)
        if not cache_root.is_absolute():
            cache_root = root / cache_root
    else:
        cache_root = root / _CACHE_DIR
    cache_root.mkdir(parents=True, exist_ok=True)
    print(f"Cache directory: {cache_root}")
    sem = asyncio.Semaphore(concurrency)

    # Pool sized to concurrency + 2 (one for the bookkeeping coroutine
    # that does sys_meta / rows fetch / periodic flush, one buffer).
    # asyncpg single-connection cannot multiplex, so concurrent
    # _build_parent_path lookups need their own connection each.
    pool_size = max(concurrency + 2, 4)
    pool = await asyncpg.create_pool(
        database_url,
        min_size=1,
        max_size=pool_size,
        statement_cache_size=0,
    )
    try:
        total_y = total_n = total_u = 0
        for sid in systems:
            y, n, u = await _run_one_system(
                pool,
                system_id=sid,
                sem=sem,
                cache_root=cache_root,
                limit=limit,
                dry_run=dry_run,
            )
            total_y += y
            total_n += n
            total_u += u
        print(
            f"\nGRAND TOTAL: yes={total_y:,} no={total_n:,} "
            f"uncertain={total_u:,}"
        )
        if total_y + total_n + total_u:
            yes_rate = 100 * total_y / (total_y + total_n + total_u)
            print(f"  yes-rate: {yes_rate:.1f}%")
    finally:
        await pool.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--systems", nargs="+", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--concurrency", type=int, default=_DEFAULT_CONCURRENCY,
        help=(
            "Parallel LLM calls. Default 4. Bump to 12 for production runs "
            "against systems with thousands of rows; verify Ollama Cloud "
            "quota first."
        ),
    )
    parser.add_argument(
        "--cache-dir", default=None,
        help=(
            "Directory for the per-system .jsonl resume cache. Defaults to "
            "data/llm_verified. Use a separate dir to A/B a new model "
            "without polluting the production cache; once happy, merge or "
            "promote the new cache."
        ),
    )
    args = parser.parse_args()
    return asyncio.run(_run(
        systems=args.systems, limit=args.limit, dry_run=args.dry_run,
        concurrency=args.concurrency, cache_dir=args.cache_dir,
    ))


if __name__ == "__main__":
    sys.exit(main())
