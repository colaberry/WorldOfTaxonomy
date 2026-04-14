"""Professional Services Firm Size and Market Segment Types domain taxonomy ingester.

Professional services firm size, market segment, and organizational structure classification.

Code prefix: dpsfirm_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
PROF_FIRM_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Global and Top-Tier Professional Services Firms --
    ("dpsfirm_big", "Global and Top-Tier Professional Services Firms", 1, None),
    ("dpsfirm_big_four", "Big 4 Accounting Firms (Deloitte, PwC, EY, KPMG)", 2, 'dpsfirm_big'),
    ("dpsfirm_big_mbb", "MBB Strategy Consulting (McKinsey, BCG, Bain)", 2, 'dpsfirm_big'),
    ("dpsfirm_big_biglaw", "AmLaw 100 Big Law Firms", 2, 'dpsfirm_big'),
    # -- Regional and Mid-Market Professional Firms --
    ("dpsfirm_regional", "Regional and Mid-Market Professional Firms", 1, None),
    ("dpsfirm_regional_acct", "Regional Accounting Firm (Grant Thornton, RSM tier)", 2, 'dpsfirm_regional'),
    ("dpsfirm_regional_consult", "Regional Management Consulting Firm", 2, 'dpsfirm_regional'),
    # -- Specialist and Boutique Advisory Firms --
    ("dpsfirm_boutique", "Specialist and Boutique Advisory Firms", 1, None),
    ("dpsfirm_boutique_specialist", "Deep-Specialty Boutique (single industry/function)", 2, 'dpsfirm_boutique'),
    ("dpsfirm_boutique_pe", "PE-Backed Consulting Roll-Up (Vista, TA Associates)", 2, 'dpsfirm_boutique'),
    # -- Solo Practitioners and Small Practices --
    ("dpsfirm_solo", "Solo Practitioners and Small Practices", 1, None),
    ("dpsfirm_solo_gig", "Freelance and Gig Economy Consultant", 2, 'dpsfirm_solo'),
    ("dpsfirm_solo_partner", "Partner-Track Small Practice (2-20 professionals)", 2, 'dpsfirm_solo'),
    # -- In-House and Captive Services Center --
    ("dpsfirm_inhouse", "In-House and Captive Services Center", 1, None),
    ("dpsfirm_inhouse_gbs", "Global Business Services (GBS) and Shared Services Center", 2, 'dpsfirm_inhouse'),
    ("dpsfirm_inhouse_corp", "Corporate Legal, Finance, or HR Function", 2, 'dpsfirm_inhouse'),
    ("dpsfirm_inhouse_coe", "Center of Excellence (CoE) for Specialized Capability", 2, 'dpsfirm_inhouse'),
    ("dpsfirm_gov", "Government and Public Sector Services", 1, None),
]

_DOMAIN_ROW = (
    "domain_prof_firm",
    "Professional Services Firm Size and Market Segment Types",
    "Professional services firm size, market segment, and organizational structure classification",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['54']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_prof_firm(conn) -> int:
    """Ingest Professional Services Firm Size and Market Segment Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_prof_firm",
        "Professional Services Firm Size and Market Segment Types",
        "Professional services firm size, market segment, and organizational structure classification",
        "1.0",
        "United States",
        "WorldOfTaxanomy",
    )

    await conn.execute(
        """INSERT INTO domain_taxonomy
               (id, name, full_name, authority, url, code_count)
           VALUES ($1, $2, $3, $4, $5, 0)
           ON CONFLICT (id) DO UPDATE SET code_count = 0""",
        *_DOMAIN_ROW,
    )

    parent_codes = {parent for _, _, _, parent in PROF_FIRM_NODES if parent is not None}

    rows = [
        (
            "domain_prof_firm",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in PROF_FIRM_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(PROF_FIRM_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_prof_firm'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_prof_firm'",
        count,
    )

    naics_codes = [
        row["code"]
        for prefix in _NAICS_PREFIXES
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE $1",
            prefix + "%",
        )
    ]

    if naics_codes:
        await conn.executemany(
            """INSERT INTO node_taxonomy_link
                   (system_id, node_code, taxonomy_id, relevance)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
            [("naics_2022", code, "domain_prof_firm", "primary") for code in naics_codes],
        )

    return count
