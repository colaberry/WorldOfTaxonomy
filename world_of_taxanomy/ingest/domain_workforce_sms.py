"""Workforce Safety Management System Types domain taxonomy ingester.

Workforce safety management system and framework classification - ISO 45001, VPP, behavior-based safety, incident reporting.

Code prefix: dwssms_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
WORKFORCE_SMS_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- ISO 45001 Occupational Health and Safety Management --
    ("dwssms_iso45001", "ISO 45001 Occupational Health and Safety Management", 1, None),
    ("dwssms_iso45001_cert", "ISO 45001 Certified (third-party audited)", 2, 'dwssms_iso45001'),
    ("dwssms_iso45001_conform", "ISO 45001 Conformance (self-declared, not certified)", 2, 'dwssms_iso45001'),
    # -- OSHA Voluntary Protection Programs (VPP) --
    ("dwssms_vpp", "OSHA Voluntary Protection Programs (VPP)", 1, None),
    ("dwssms_vpp_star", "VPP Star Site (top-tier OSHA recognition)", 2, 'dwssms_vpp'),
    ("dwssms_vpp_merit", "VPP Merit Site (working toward Star)", 2, 'dwssms_vpp'),
    # -- Behavior-Based Safety (BBS) Programs --
    ("dwssms_behavbased", "Behavior-Based Safety (BBS) Programs", 1, None),
    ("dwssms_behavbased_obs", "Safety Observation and Reporting System", 2, 'dwssms_behavbased'),
    ("dwssms_behavbased_near", "Near-Miss Reporting and Leading Indicator Tracking", 2, 'dwssms_behavbased'),
    # -- Incident Investigation and Root Cause Analysis --
    ("dwssms_incident", "Incident Investigation and Root Cause Analysis", 1, None),
    ("dwssms_incident_rca", "Root Cause Analysis (5-Why, Fishbone, TapRoot)", 2, 'dwssms_incident'),
    ("dwssms_incident_osha300", "OSHA 300 Log and Recordkeeping Compliance", 2, 'dwssms_incident'),
    # -- Industry-Specific Safety Management Programs --
    ("dwssms_industry", "Industry-Specific Safety Management Programs", 1, None),
    ("dwssms_industry_isnetworld", "ISNetworld and PICS Contractor Safety Pre-qualification", 2, 'dwssms_industry'),
    ("dwssms_industry_csms", "Contractor Safety Management System (oil and gas SEMS)", 2, 'dwssms_industry'),
]

_DOMAIN_ROW = (
    "domain_workforce_sms",
    "Workforce Safety Management System Types",
    "Workforce safety management system and framework classification - ISO 45001, VPP, behavior-based safety, incident reporting",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11", "21", "22", "23", "31", "32", "33", "42", "44", "45", "48", "49", "51", "52", "53", "54", "55", "56", "61", "62", "71", "72", "81", "92"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_workforce_sms(conn) -> int:
    """Ingest Workforce Safety Management System Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_workforce_sms",
        "Workforce Safety Management System Types",
        "Workforce safety management system and framework classification - ISO 45001, VPP, behavior-based safety, incident reporting",
        "1.0",
        "Global",
        "WorldOfTaxanomy",
    )

    await conn.execute(
        """INSERT INTO domain_taxonomy
               (id, name, full_name, authority, url, code_count)
           VALUES ($1, $2, $3, $4, $5, 0)
           ON CONFLICT (id) DO UPDATE SET code_count = 0""",
        *_DOMAIN_ROW,
    )

    parent_codes = {parent for _, _, _, parent in WORKFORCE_SMS_NODES if parent is not None}

    rows = [
        (
            "domain_workforce_sms",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in WORKFORCE_SMS_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(WORKFORCE_SMS_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_workforce_sms'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_workforce_sms'",
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
            [("naics_2022", code, "domain_workforce_sms", "primary") for code in naics_codes],
        )

    return count
