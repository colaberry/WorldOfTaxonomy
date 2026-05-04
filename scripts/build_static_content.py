#!/usr/bin/env python3
"""Build static text dumps of every classification system for AEO + RAG.

Output layout (relative to project root):
    frontend/public/llms-codes/
        index.txt              master index of systems -> chunk URLs
        .manifest.json         per-system content hash; skip rebuild if unchanged
        <system>.txt           for systems whose dump fits in one file
        <system>/<chunk>.txt   for big systems, chunked by top-level code prefix

Each line in a system file:
    [code] title -- description :: target_system:target_code, ...

Re-runs are no-ops for systems whose content hash has not changed, so this is
safe to wire into every dev build.

Usage:
    python3 scripts/build_static_content.py
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUT_DIR = PROJECT_ROOT / "frontend" / "public" / "llms-codes"
MAX_FILE_BYTES = 5 * 1024 * 1024
SITE_URL = "https://worldoftaxonomy.com"


def _format_node(code: str, title: str, description: str | None, equivs: list[str]) -> str:
    desc = (description or "").replace("\r", " ").replace("\n", " ").strip()
    out = f"[{code}] {title}"
    if desc:
        out += f" -- {desc}"
    if equivs:
        out += f" :: {', '.join(equivs)}"
    return out


def _chunk_by_top_level(content: str) -> list[tuple[str, str]]:
    """Group lines into <5MB chunks keyed by the first 1-3 chars of the code."""
    by_first: dict[str, list[str]] = {}
    for line in content.splitlines():
        if not line.startswith("["):
            continue
        code = line[1:].split("]", 1)[0]
        key = (code[:1] or "_").upper()
        by_first.setdefault(key, []).append(line)

    out: list[tuple[str, str]] = []
    for key, lines in sorted(by_first.items()):
        text = "\n".join(lines) + "\n"
        if len(text.encode("utf-8")) <= MAX_FILE_BYTES:
            out.append((_safe_key(key), text))
            continue
        # Sub-chunk by two chars when one prefix is too big.
        sub: dict[str, list[str]] = {}
        for ln in lines:
            code = ln[1:].split("]", 1)[0]
            sk = (code[:2] or code or "_").upper()
            sub.setdefault(sk, []).append(ln)
        for sk, slines in sorted(sub.items()):
            out.append((_safe_key(sk), "\n".join(slines) + "\n"))
    return out


def _safe_key(key: str) -> str:
    """Make a code prefix filesystem-safe."""
    return "".join(c if c.isalnum() else "_" for c in key) or "_"


async def _fetch_system_content(conn, system_id: str) -> tuple[str, int]:
    nodes = await conn.fetch(
        """
        select code, title, description
        from classification_node
        where system_id = $1
        order by code
        """,
        system_id,
    )
    equiv_rows = await conn.fetch(
        """
        select source_code, target_system, target_code
        from equivalence
        where source_system = $1
        order by source_code, target_system, target_code
        """,
        system_id,
    )
    equiv_by_code: dict[str, list[str]] = {}
    for r in equiv_rows:
        equiv_by_code.setdefault(r["source_code"], []).append(
            f"{r['target_system']}:{r['target_code']}"
        )
    lines = [
        _format_node(
            n["code"], n["title"], n["description"], equiv_by_code.get(n["code"], [])
        )
        for n in nodes
    ]
    body = "\n".join(lines) + ("\n" if lines else "")
    return body, len(nodes)


async def _list_systems(conn) -> list[str]:
    only = os.environ.get("BUILD_STATIC_ONLY", "").strip()
    if only:
        wanted = [s.strip() for s in only.split(",") if s.strip()]
        rows = await conn.fetch(
            "select id from classification_system where id = any($1::text[]) order by id",
            wanted,
        )
    else:
        rows = await conn.fetch("select id from classification_system order by id")
    return [r["id"] for r in rows]


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _clean_stale(out_dir: Path, system_id: str) -> None:
    flat = out_dir / f"{system_id}.txt"
    if flat.exists():
        flat.unlink()
    sys_dir = out_dir / system_id
    if sys_dir.is_dir():
        for p in sys_dir.glob("*.txt"):
            p.unlink()


async def main() -> int:
    if not os.environ.get("DATABASE_URL"):
        print(
            "build_static_content: DATABASE_URL not set; skipping (CI/no-DB env).",
            file=sys.stderr,
        )
        return 0

    # Lazy import so a missing DATABASE_URL does not crash on dotenv load
    from world_of_taxonomy.db import close_pool, get_pool

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / ".manifest.json"
    manifest: dict = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {}

    pool = await get_pool()
    rebuilt: list[str] = []
    skipped: list[str] = []
    index_lines: list[str] = [
        "# WorldOfTaxonomy static code dumps",
        "# One file per classification system (chunked when >5MB).",
        "# Line format: [code] title -- description :: target_system:target_code, ...",
        "",
    ]

    try:
        async with pool.acquire() as conn:
            systems = await _list_systems(conn)
            for system_id in systems:
                content, node_count = await _fetch_system_content(conn, system_id)
                chash = _content_hash(content)
                entry = manifest.get(system_id, {})
                unchanged = (
                    entry.get("hash") == chash
                    and entry.get("files")
                    and all((OUT_DIR / f).exists() for f in entry["files"])
                )

                size = len(content.encode("utf-8"))
                if size <= MAX_FILE_BYTES:
                    files = [(f"{system_id}.txt", content)]
                else:
                    files = [
                        (f"{system_id}/{key}.txt", chunk)
                        for key, chunk in _chunk_by_top_level(content)
                    ]

                if unchanged:
                    skipped.append(system_id)
                else:
                    _clean_stale(OUT_DIR, system_id)
                    for rel, body in files:
                        path = OUT_DIR / rel
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(body)
                    rebuilt.append(system_id)

                manifest[system_id] = {
                    "hash": chash,
                    "nodes": node_count,
                    "bytes": size,
                    "files": [rel for rel, _ in files],
                }
                for rel, _ in files:
                    index_lines.append(f"{system_id}: {SITE_URL}/llms-codes/{rel}")
    finally:
        await close_pool()

    (OUT_DIR / "index.txt").write_text("\n".join(index_lines) + "\n")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(
        f"build_static_content: rebuilt={len(rebuilt)} "
        f"skipped={len(skipped)} systems={len(skipped) + len(rebuilt)}"
    )
    if rebuilt:
        preview = ", ".join(rebuilt[:8])
        more = f" (+{len(rebuilt) - 8} more)" if len(rebuilt) > 8 else ""
        print(f"  changed: {preview}{more}")
    return 0


def _entrypoint() -> int:
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(_entrypoint())
