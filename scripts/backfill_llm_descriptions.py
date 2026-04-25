"""Generate descriptions via LLM for a curated allowlist of skeleton
reference taxonomies (OWASP Top 10, APGAR Score, Bristol Stool, etc.).

The output is cached as JSONL under ``data/llm_descriptions/<system_id>.jsonl``
so re-runs skip already-generated rows. After generation the cache is
applied to the DB via ``apply_descriptions`` (NULL-only).

Usage:

    python3 -m scripts.backfill_llm_descriptions --dry-run
    python3 -m scripts.backfill_llm_descriptions --systems owasp_top10
    python3 -m scripts.backfill_llm_descriptions
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.llm_descriptions import (
    build_messages,
    sanitize_response,
)
from world_of_taxonomy.llm_client import chat_json


_CACHE_DIR = Path("data/llm_descriptions")
_CONCURRENCY = 4

# Curated allowlist of well-known reference taxonomies that have factual
# 1-2 sentence definitions in widely cited public sources. This list
# excludes the auto-generated "domain_*" synthetic taxonomies, which
# would risk hallucination.
_ALLOWLIST: List[str] = [
    "owasp_top10",
    "apgar_score",
    "bmi_categories",
    "bristol_stool",
    "pain_scale",
    "saffir_simpson",
    "fujita_tornado",
    "mohs_hardness",
    "uv_index",
    "richter_scale",
    "earthquake_magnitude",
    "asa_physical",
    "blood_types_abo",
    "haccp",
    "cms_star",
    "ftse_icb_detail",
    "mitre_attack",
    "cve_cwe",
    "tcfd",
    "ssbti_categories",
    "sbti_categories",
    "issb_s1_s2",
    "owasp",
    "ietf_rfc",
    "w3c",
    "ieee_standards",
    "ietf_rfc_categories",
    "iab_content",
    "togaf",
    "archimate",
    "prince2",
    "cobit",
    "esco_qualifications",
    "eqf",
    "aqf",
    "nqf",
    "isco_skill_levels",
    "icf",
    "nfpa_codes",
    "ifrs",
    "fasb_standards",
    "ihs_levels",
    "dewey_decimal",
    "udc",
    "lcsh_skel",
    "msc_2020",
    "pacs",
    "lcc",
    "schedule_b",
    "ecn",
    "eccn",
    "ral_colors",
    "pantone_families",
    "isrc_format",
    "isbn_groups",
    "mime_types",
    "http_status",
    "spdx_licenses",
    "periodic_table",
    "geological_timescale",
    "beaufort_wind",
    "bloomberg_bics",
    "refinitiv_trbc",
    "ftse_icb",
    "icb",
    "olympic_sports",
    "fifa_confederations",
    "world_skills",
    "wcag_2_2",
    "six_sigma",
    "lean_tools",
    "ai_ml_models",
    "cncf",
    "sdg_global_indicators",
    "unicode_emoji",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _cache_path(system_id: str) -> Path:
    return _CACHE_DIR / f"{system_id}.jsonl"


def _load_cache(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
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
            desc = rec.get("description") or ""
            if code and desc:
                out[code] = desc
    return out


def _append_cache(path: Path, code: str, description: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"code": code, "description": description}) + "\n")


async def _generate_one(
    sem: asyncio.Semaphore,
    *,
    system_name: str,
    code: str,
    title: str,
) -> str:
    """Try up to 3 times if the LLM returns an empty body or transient
    error. Empty responses sometimes come back from Ollama Cloud under
    load; a single retry usually clears them.
    """
    async with sem:
        for attempt in range(3):
            try:
                raw = await chat_json(
                    build_messages(
                        system_name=system_name, code=code, title=title,
                    ),
                    max_tokens=400,
                    temperature=0.2 if attempt > 0 else 0.0,
                    timeout=60.0,
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"    LLM error for {code} (attempt {attempt+1}): {exc}",
                    file=sys.stderr,
                )
                await asyncio.sleep(1.0 + attempt)
                continue
            sanitized = sanitize_response(raw)
            if sanitized:
                return sanitized
            # Empty/refusal: brief backoff then retry with slightly higher
            # temperature to escape any deterministic refusal mode.
            await asyncio.sleep(0.5 + attempt)
    return ""


async def _backfill_system(
    conn,
    *,
    system_id: str,
    cache_root: Path,
    sem: asyncio.Semaphore,
    dry_run: bool,
    only_leaves: bool,
) -> int:
    sys_meta = await conn.fetchrow(
        "SELECT id, full_name, name FROM classification_system WHERE id = $1",
        system_id,
    )
    if not sys_meta:
        return 0
    system_name = sys_meta["full_name"] or sys_meta["name"] or system_id

    rows = await conn.fetch(
        "SELECT code, title FROM classification_node "
        "WHERE system_id = $1 AND (description IS NULL OR description = '') "
        "ORDER BY code",
        system_id,
    )
    if not rows:
        return 0

    cache_path = cache_root / f"{system_id}.jsonl"
    cached = _load_cache(cache_path)

    to_generate = [
        (r["code"], r["title"])
        for r in rows
        if r["code"] not in cached
    ]
    print(
        f"  {system_id}: {len(rows)} empty rows, "
        f"{len(cached)} cached, {len(to_generate)} to generate"
    )

    if dry_run:
        return len(rows)

    # Generate missing
    new_count = 0
    for code, title in to_generate:
        desc = await _generate_one(
            sem, system_name=system_name, code=code, title=title,
        )
        if desc:
            _append_cache(cache_path, code, desc)
            cached[code] = desc
            new_count += 1
    print(f"    generated {new_count} new descriptions")

    # Apply cache to DB
    updated = await apply_descriptions(conn, system_id, cached)
    print(f"    applied {updated} to DB")
    return updated


async def _run(
    *,
    dry_run: bool,
    only_systems: Optional[List[str]],
) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1
    if not (os.environ.get("OLLAMA_API_KEY") or os.environ.get("OPENROUTER_API_KEY")):
        print("ERROR: no LLM provider configured", file=sys.stderr)
        return 1

    cache_root = root / _CACHE_DIR
    cache_root.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(_CONCURRENCY)

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        # Filter allowlist to systems that exist in this DB
        existing = {
            r["id"]
            for r in await conn.fetch("SELECT id FROM classification_system")
        }
        targets = [s for s in _ALLOWLIST if s in existing]
        if only_systems:
            targets = [s for s in targets if s in set(only_systems)]
        print(f"  Target systems: {len(targets)}")

        total = 0
        for sid in targets:
            updated = await _backfill_system(
                conn,
                system_id=sid,
                cache_root=cache_root,
                sem=sem,
                dry_run=dry_run,
                only_leaves=False,
            )
            total += updated
        print(f"\n  Total {'would-update' if dry_run else 'updated'}: {total}")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--systems",
        nargs="+",
        help="Restrict to specific system IDs (must be in allowlist).",
    )
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run, only_systems=args.systems))


if __name__ == "__main__":
    sys.exit(main())
