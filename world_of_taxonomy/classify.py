"""Classification engine - match free-text against taxonomy systems.

Phase 1: PostgreSQL full-text search using the existing search_vector
(tsvector) on classification_node. Fast, deterministic, zero cost per query.
"""

from __future__ import annotations

import re
from typing import Optional

from world_of_taxonomy.category import compute_edge_kind
from world_of_taxonomy.classify_synonyms import expand_query as _expand_wiki_synonyms
from world_of_taxonomy import classify_llm as _llm_mod

# Default systems to search when none specified
DEFAULT_SYSTEMS = [
    'naics_2022', 'isic_rev4', 'nace_rev2', 'hs_2022',
    'soc_2018', 'isco_08', 'cpc_v21', 'icd10cm', 'icd_11',
    'unspsc_v24', 'esco_occupations', 'esco_skills',
    'sic_1987', 'anzsic_2006', 'anzsco_2022',
]

# Mirrors frontend/src/lib/server-api.ts STOPWORDS. Generic descriptors that
# appear in user queries but rarely in official classification titles.
_STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'also', 'sells', 'company', 'service',
    'services', 'online', 'based', 'independent', 'private', 'retail', 'small',
    'commercial', 'residential', 'from', 'into', 'over', 'under', 'using',
    'provider', 'platform', 'startup', 'shop', 'store', 'agency', 'firm',
    'business', 'general', 'custom', 'local', 'mobile', 'full', 'this',
}

_SPLIT_RX = re.compile(r"[^a-z0-9]+")


def _extract_significant_terms(query: str) -> list[str]:
    tokens: list[str] = []
    for tok in _SPLIT_RX.split(query.lower()):
        if len(tok) >= 4 and tok not in _STOPWORDS:
            tokens.append(tok)
    # Longest tokens first: they are usually the most specific.
    tokens.sort(key=len, reverse=True)
    # De-dupe while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


_SANITIZE_TSQ_RX = re.compile(r"[^a-z0-9]+")


def _sanitize_tsquery_token(tok: str) -> str:
    """Collapse a phrase ("ambulatory health") into a single safe token for
    to_tsquery. We OR the collapsed form via the & operator so multi-word
    synonyms stay coherent ('ambulatory & health')."""
    parts = [p for p in _SANITIZE_TSQ_RX.split(tok.lower()) if len(p) >= 2]
    return " & ".join(parts)


def _build_or_tsquery(
    query: str,
    max_terms: int = 6,
    extra_synonyms: Optional[list[str]] = None,
) -> Optional[str]:
    """Compose an OR tsquery from the query's significant tokens plus any
    wiki-curated synonym expansions for modern business terms.

    `extra_synonyms` lets the LLM fallback inject additional keywords after
    the first pass returns zero results across every target system.
    """
    terms = _extract_significant_terms(query)[:max_terms]
    synonym_terms = list(_expand_wiki_synonyms(query))
    if extra_synonyms:
        synonym_terms.extend(extra_synonyms)

    clauses: list[str] = []
    seen: set[str] = set()
    for t in terms:
        safe = _sanitize_tsquery_token(t)
        if safe and safe not in seen:
            seen.add(safe)
            clauses.append(safe)
    for s in synonym_terms:
        safe = _sanitize_tsquery_token(s)
        if safe and safe not in seen:
            seen.add(safe)
            clauses.append(safe)

    if not clauses:
        return None
    return " | ".join(f"({c})" for c in clauses)


# Compound-business detection. A real-world description often enumerates
# multiple businesses under one roof ("gas station + bakery + pharmacy").
# NAICS/ISIC treat each as a separate establishment; the response must
# reflect that so downstream workflows (SBA loan, KYC, tax) see every line.
#
# The segmenter is rule-based on purpose: deterministic, zero-latency,
# easy to test. An LLM segmenter can replace this behind the same interface.
_OPENER_RX = re.compile(
    r"^\s*(?:we(?:'re|\s+are|\s+have|\s+run|\s+own|\s+operate|\s+offer)|our\s+business\s+is|i\s+(?:run|own|operate|have))\s+",
    re.IGNORECASE,
)
_TRAILING_RX = re.compile(r"\s+all\s+in\s+one\s*\.?\s*$", re.IGNORECASE)
_CONJ_RX = re.compile(r"\s+and\s+|\s*,\s*|\s*;\s*|\s+plus\s+|\s+also\s+", re.IGNORECASE)
# Strip leading article + noise phrases from each atom.
_ATOM_NOISE_RX = re.compile(
    r"^(?:an?\s+|the\s+|that\s+(?:sells|has|does|offers|runs)\s+|has\s+a\s+|sells\s+a\s+|with\s+a\s+|plus\s+a?\s*)",
    re.IGNORECASE,
)

_COMPOUND_MIN_ATOMS = 3


def _segment_query(text: str) -> list[str]:
    """Split a free-text description into candidate business atoms."""
    cleaned = _OPENER_RX.sub("", text.strip())
    cleaned = _TRAILING_RX.sub("", cleaned)
    raw_parts = _CONJ_RX.split(cleaned)
    atoms: list[str] = []
    seen: set[str] = set()
    for part in raw_parts:
        atom = _ATOM_NOISE_RX.sub("", part).strip(" .,/")
        if len(atom) < 3:
            continue
        key = atom.lower()
        if key in seen:
            continue
        seen.add(key)
        atoms.append(atom)
    return atoms


def _is_compound(atoms: list[str]) -> bool:
    return len(atoms) >= _COMPOUND_MIN_ATOMS

DISCLAIMER = (
    "Results are informational only and not guaranteed to be accurate "
    "or complete. Use at your own risk. For authoritative codes, "
    "consult the official source."
)

REPORT_ISSUE_URL = (
    "https://github.com/colaberry/WorldOfTaxonomy/issues/new"
    "?template=data_issue.yml&labels=data-issue"
)


async def _classify_single(
    conn,
    text: str,
    target_systems: list[str],
    limit: int,
) -> list[dict]:
    """Run the full-text search (plainto + OR fallback) across the given systems.

    Returns the per-system matches list; does not populate crosswalks or
    metadata (the caller composes the response envelope).
    """
    or_tsquery = _build_or_tsquery(text)
    results: list[dict] = []
    for sys_id in target_systems:
        rows = await conn.fetch(
            """
            SELECT code, title, level,
                   ts_rank_cd(search_vector, plainto_tsquery('english', $2)) AS score
            FROM classification_node
            WHERE system_id = $1
              AND search_vector @@ plainto_tsquery('english', $2)
            ORDER BY score DESC
            LIMIT $3
            """,
            sys_id,
            text,
            limit,
        )

        if not rows and or_tsquery:
            rows = await conn.fetch(
                """
                SELECT code, title, level,
                       ts_rank_cd(search_vector, to_tsquery('english', $2)) AS score
                FROM classification_node
                WHERE system_id = $1
                  AND search_vector @@ to_tsquery('english', $2)
                ORDER BY score DESC
                LIMIT $3
                """,
                sys_id,
                or_tsquery,
                limit,
            )

        if rows:
            sys_row = await conn.fetchrow(
                "SELECT name FROM classification_system WHERE id = $1",
                sys_id,
            )
            sys_name = sys_row["name"] if sys_row else sys_id
            results.append({
                "system_id": sys_id,
                "system_name": sys_name,
                "results": [
                    {
                        "code": r["code"],
                        "title": r["title"],
                        "score": round(float(r["score"]), 4),
                        "level": r["level"],
                    }
                    for r in rows
                ],
            })
    return results


async def _classify_with_tsquery(
    conn,
    text: str,
    target_systems: list[str],
    limit: int,
    tsquery: str,
) -> list[dict]:
    """Run a pre-built to_tsquery across systems. Used by the LLM fallback
    after the deterministic pipeline (plainto + wiki OR) returned nothing."""
    results: list[dict] = []
    for sys_id in target_systems:
        rows = await conn.fetch(
            """
            SELECT code, title, level,
                   ts_rank_cd(search_vector, to_tsquery('english', $2)) AS score
            FROM classification_node
            WHERE system_id = $1
              AND search_vector @@ to_tsquery('english', $2)
            ORDER BY score DESC
            LIMIT $3
            """,
            sys_id,
            tsquery,
            limit,
        )
        if not rows:
            continue
        sys_row = await conn.fetchrow(
            "SELECT name FROM classification_system WHERE id = $1",
            sys_id,
        )
        sys_name = sys_row["name"] if sys_row else sys_id
        results.append({
            "system_id": sys_id,
            "system_name": sys_name,
            "results": [
                {
                    "code": r["code"],
                    "title": r["title"],
                    "score": round(float(r["score"]), 4),
                    "level": r["level"],
                }
                for r in rows
            ],
        })
    return results


async def _classify_domains(
    conn,
    text: str,
    limit_per_system: int = 3,
    max_systems: int = 8,
) -> list[dict]:
    """Unified FTS across all domain_* systems in a single round-trip.

    Uses a window function to pick top-N per system. Domain systems are
    narrow and numerous (400+), so a per-system loop would be slow; this
    caps to the most relevant `max_systems` by peak score.
    """
    or_tsquery = _build_or_tsquery(text)

    rows = await conn.fetch(
        """
        WITH hits AS (
            SELECT n.system_id, n.code, n.title, n.level,
                   ts_rank_cd(n.search_vector, plainto_tsquery('english', $1)) AS score,
                   ROW_NUMBER() OVER (
                       PARTITION BY n.system_id
                       ORDER BY ts_rank_cd(n.search_vector, plainto_tsquery('english', $1)) DESC
                   ) AS rn
            FROM classification_node n
            WHERE n.system_id LIKE 'domain\\_%%' ESCAPE '\\'
              AND n.search_vector @@ plainto_tsquery('english', $1)
        ),
        top_systems AS (
            SELECT system_id, MAX(score) AS peak
            FROM hits
            GROUP BY system_id
            ORDER BY peak DESC
            LIMIT $2
        )
        SELECT h.system_id, s.name AS system_name,
               h.code, h.title, h.level, h.score, h.rn
        FROM hits h
        JOIN top_systems ts ON ts.system_id = h.system_id
        JOIN classification_system s ON s.id = h.system_id
        WHERE h.rn <= $3
        ORDER BY ts.peak DESC, h.system_id, h.rn
        """,
        text,
        max_systems,
        limit_per_system,
    )

    if not rows and or_tsquery:
        rows = await conn.fetch(
            """
            WITH hits AS (
                SELECT n.system_id, n.code, n.title, n.level,
                       ts_rank_cd(n.search_vector, to_tsquery('english', $1)) AS score,
                       ROW_NUMBER() OVER (
                           PARTITION BY n.system_id
                           ORDER BY ts_rank_cd(n.search_vector, to_tsquery('english', $1)) DESC
                       ) AS rn
                FROM classification_node n
                WHERE n.system_id LIKE 'domain\\_%%' ESCAPE '\\'
                  AND n.search_vector @@ to_tsquery('english', $1)
            ),
            top_systems AS (
                SELECT system_id, MAX(score) AS peak
                FROM hits
                GROUP BY system_id
                ORDER BY peak DESC
                LIMIT $2
            )
            SELECT h.system_id, s.name AS system_name,
                   h.code, h.title, h.level, h.score, h.rn
            FROM hits h
            JOIN top_systems ts ON ts.system_id = h.system_id
            JOIN classification_system s ON s.id = h.system_id
            WHERE h.rn <= $3
            ORDER BY ts.peak DESC, h.system_id, h.rn
            """,
            or_tsquery,
            max_systems,
            limit_per_system,
        )

    # Group rows by system_id, preserving peak-score ordering.
    grouped: dict[str, dict] = {}
    for r in rows:
        sid = r["system_id"]
        if sid not in grouped:
            grouped[sid] = {
                "system_id": sid,
                "system_name": r["system_name"],
                "results": [],
            }
        grouped[sid]["results"].append({
            "code": r["code"],
            "title": r["title"],
            "score": round(float(r["score"]), 4),
            "level": r["level"],
        })
    return list(grouped.values())


async def _classify_domains_with_tsquery(
    conn,
    tsquery: str,
    limit_per_system: int = 3,
    max_systems: int = 8,
) -> list[dict]:
    """Unified to_tsquery FTS over domain_* systems. Used by LLM fallback."""
    rows = await conn.fetch(
        """
        WITH hits AS (
            SELECT n.system_id, n.code, n.title, n.level,
                   ts_rank_cd(n.search_vector, to_tsquery('english', $1)) AS score,
                   ROW_NUMBER() OVER (
                       PARTITION BY n.system_id
                       ORDER BY ts_rank_cd(n.search_vector, to_tsquery('english', $1)) DESC
                   ) AS rn
            FROM classification_node n
            WHERE n.system_id LIKE 'domain\\_%%' ESCAPE '\\'
              AND n.search_vector @@ to_tsquery('english', $1)
        ),
        top_systems AS (
            SELECT system_id, MAX(score) AS peak
            FROM hits
            GROUP BY system_id
            ORDER BY peak DESC
            LIMIT $2
        )
        SELECT h.system_id, s.name AS system_name,
               h.code, h.title, h.level, h.score, h.rn
        FROM hits h
        JOIN top_systems ts ON ts.system_id = h.system_id
        JOIN classification_system s ON s.id = h.system_id
        WHERE h.rn <= $3
        ORDER BY ts.peak DESC, h.system_id, h.rn
        """,
        tsquery,
        max_systems,
        limit_per_system,
    )
    grouped: dict[str, dict] = {}
    for r in rows:
        sid = r["system_id"]
        if sid not in grouped:
            grouped[sid] = {
                "system_id": sid,
                "system_name": r["system_name"],
                "results": [],
            }
        grouped[sid]["results"].append({
            "code": r["code"],
            "title": r["title"],
            "score": round(float(r["score"]), 4),
            "level": r["level"],
        })
    return list(grouped.values())


def _compound_cta(atom_count: int) -> dict:
    return {
        "title": f"{atom_count} business lines detected",
        "message": (
            "Compound classifications affect NAICS primary-code selection, "
            "SBA loan eligibility, and multi-state tax filings. A short "
            "consultation ensures every line is filed correctly."
        ),
        "url": "/contact?topic=compound-classification",
        "cta_label": "Book a 15-min consultation",
    }


async def classify_text(
    conn,
    text: str,
    system_ids: Optional[list[str]] = None,
    limit: int = 5,
) -> dict:
    """Classify free-text against classification systems using full-text search.

    Returns top matches per system with relevance scores. When the query
    enumerates multiple businesses (e.g. "bakery and pharmacy and hotel"),
    returns a compound response with one atom per detected line of business.
    """
    target_systems = system_ids or DEFAULT_SYSTEMS

    # Validate limit
    limit = max(1, min(limit, 20))

    atoms = _segment_query(text)
    if _is_compound(atoms):
        atom_payload: list[dict] = []
        for atom in atoms:
            standard_matches = await _classify_single(conn, atom, target_systems, limit)
            domain_matches = await _classify_domains(conn, atom, limit_per_system=limit)
            # Domain matches lead; standards follow. Consumers can re-partition
            # on system_id prefix (domain_*) if they need the explicit split.
            matches = domain_matches + standard_matches
            atom_payload.append({"phrase": atom, "matches": matches})
        # Hero = first atom with non-empty matches; falls back to first atom.
        hero = next(
            (a for a in atom_payload if a["matches"]),
            atom_payload[0] if atom_payload else None,
        )
        return {
            "query": text,
            "compound": True,
            "atoms": atom_payload,
            "hero": hero,
            "matches": hero["matches"] if hero else [],
            "crosswalks": [],
            "cta": _compound_cta(len(atom_payload)),
            "disclaimer": DISCLAIMER,
            "report_issue_url": REPORT_ISSUE_URL,
        }

    standard_results = await _classify_single(conn, text, target_systems, limit)
    domain_results = await _classify_domains(conn, text, limit_per_system=limit)
    results = domain_results + standard_results

    # LLM fallback: if every target system returned zero matches, consult the
    # LLM for expansion keywords and retry once. Keeps costs minimal - paid
    # only on the ~5% of queries the deterministic layers can't resolve.
    llm_used = False
    llm_keywords: list[str] = []
    if not results:
        llm_keywords = await _llm_mod.expand_via_llm(text)
        if llm_keywords:
            llm_used = True
            llm_tsquery = _build_or_tsquery(text, extra_synonyms=llm_keywords)
            if llm_tsquery:
                standard_retry = await _classify_with_tsquery(
                    conn, text, target_systems, limit, llm_tsquery
                )
                domain_retry = await _classify_domains_with_tsquery(
                    conn, llm_tsquery, limit_per_system=limit
                )
                results = domain_retry + standard_retry

    # Fetch crosswalk edges between top results
    crosswalks = []
    if len(results) >= 2:
        # Collect all top codes per system
        code_map: dict[str, list[str]] = {}
        for match in results:
            code_map[match["system_id"]] = [
                r["code"] for r in match["results"][:3]
            ]

        sys_ids = list(code_map.keys())
        for i, sys_a in enumerate(sys_ids):
            for sys_b in sys_ids[i + 1:]:
                codes_a = code_map[sys_a]
                codes_b = code_map[sys_b]
                edges = await conn.fetch(
                    """
                    SELECT source_system, source_code, target_system,
                           target_code, match_type
                    FROM equivalence
                    WHERE (source_system = $1 AND source_code = ANY($2::text[])
                           AND target_system = $3 AND target_code = ANY($4::text[]))
                       OR (source_system = $3 AND source_code = ANY($4::text[])
                           AND target_system = $1 AND target_code = ANY($2::text[]))
                    LIMIT 10
                    """,
                    sys_a,
                    codes_a,
                    sys_b,
                    codes_b,
                )
                for e in edges:
                    crosswalks.append({
                        "from": f"{e['source_system']}:{e['source_code']}",
                        "to": f"{e['target_system']}:{e['target_code']}",
                        "match_type": e["match_type"],
                        "edge_kind": compute_edge_kind(
                            e["source_system"], e["target_system"]
                        ),
                    })

    return {
        "query": text,
        "compound": False,
        "matches": results,
        "crosswalks": crosswalks,
        "disclaimer": DISCLAIMER,
        "report_issue_url": REPORT_ISSUE_URL,
        "llm_used": llm_used,
        "llm_keywords": llm_keywords if llm_used else [],
    }
