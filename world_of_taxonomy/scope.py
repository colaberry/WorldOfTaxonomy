"""Country-aware scope resolution for search and classify.

A single source of truth for translating a list of ISO 3166-1 country codes
into the two buckets of classification systems the API and MCP surfaces
return: `country_specific_systems` (official / regional) and
`global_standard_systems` (recommended universal standards). Callers use
`candidate_systems` as the union for downstream search.
"""

from __future__ import annotations

from typing import Optional


async def resolve_country_scope(
    conn,
    countries: Optional[list[str]],
) -> Optional[dict]:
    """Return country-aware candidate systems partitioned by relevance.

    Args:
        conn: asyncpg connection.
        countries: list of ISO 3166-1 alpha-2 country codes (case-insensitive).
                   Empty or None means no scope was requested.

    Returns:
        None if no scope was requested. Otherwise a dict with:
          - countries: normalized upper-case country codes actually requested
          - country_specific_systems: system IDs with relevance official/regional
            for any of the requested countries (dedup'd, sorted)
          - global_standard_systems: system IDs with relevance recommended
            for any of the requested countries (dedup'd, sorted)
          - candidate_systems: union of both buckets (dedup'd, sorted)

        Historical systems are excluded. Unknown country codes yield empty
        buckets rather than an error - the scope was requested, there's
        just nothing applicable.
    """
    if not countries:
        return None

    normalized = sorted({c.upper() for c in countries if c and c.strip()})
    if not normalized:
        return None

    rows = await conn.fetch(
        """SELECT DISTINCT system_id, relevance
           FROM country_system_link
           WHERE country_code = ANY($1::text[])
             AND relevance IN ('official', 'regional', 'recommended')""",
        normalized,
    )

    country_specific: set[str] = set()
    global_standards: set[str] = set()
    for row in rows:
        if row["relevance"] in ("official", "regional"):
            country_specific.add(row["system_id"])
        elif row["relevance"] == "recommended":
            global_standards.add(row["system_id"])

    country_list = sorted(country_specific)
    global_list = sorted(global_standards)
    return {
        "countries": normalized,
        "country_specific_systems": country_list,
        "global_standard_systems": global_list,
        "candidate_systems": sorted(set(country_list) | set(global_list)),
    }
