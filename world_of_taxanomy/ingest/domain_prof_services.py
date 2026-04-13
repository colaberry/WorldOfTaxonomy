"""Professional Services domain taxonomy ingester.

Professional services taxonomy organizes service lines (NAICS 54):
  Service Line     (dps_line*)   - legal, accounting, consulting, engineering, marketing
  Engagement Type  (dps_engage*) - project, retainer, advisory, staff augmentation
  Billing Model    (dps_bill*)   - hourly, fixed-fee, contingency, value-based
  Certification    (dps_cert*)   - CPA, JD, PE, PMP, CFA, MD/DO

Source: NAICS 54 subsectors + AICPA/ABA/ACEC professional association frameworks.
Public domain. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
PROF_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Service Line category --
    ("dps_line",         "Professional Service Line",                            1, None),
    ("dps_line_legal",   "Legal Services (law firm, corporate counsel)",        2, "dps_line"),
    ("dps_line_acct",    "Accounting and Audit (CPA firm, tax advisory)",       2, "dps_line"),
    ("dps_line_consult", "Management Consulting (strategy, operations, IT)",   2, "dps_line"),
    ("dps_line_eng",     "Engineering and Technical Services (civil, mech, EE)",2, "dps_line"),
    ("dps_line_mktg",    "Marketing, Advertising and PR Agency",                2, "dps_line"),
    ("dps_line_research","Research and Development Services",                   2, "dps_line"),

    # -- Engagement Type category --
    ("dps_engage",          "Engagement Type",                                   1, None),
    ("dps_engage_project",  "Project-Based Engagement (fixed scope, deadline)", 2, "dps_engage"),
    ("dps_engage_retainer", "Retainer and Ongoing Advisory",                   2, "dps_engage"),
    ("dps_engage_advisory", "Board Advisory and Expert Witness",                2, "dps_engage"),
    ("dps_engage_staff",    "Staff Augmentation (contract, nearshore, offshore)",2, "dps_engage"),

    # -- Billing Model category --
    ("dps_bill",           "Billing and Fee Model",                              1, None),
    ("dps_bill_hourly",    "Hourly Rate (billable hours, timesheet-based)",     2, "dps_bill"),
    ("dps_bill_fixed",     "Fixed Fee (project price, lump sum)",               2, "dps_bill"),
    ("dps_bill_contingent","Contingency Fee (success-based, percentage)",       2, "dps_bill"),
    ("dps_bill_value",     "Value-Based Pricing (outcome and ROI-linked)",      2, "dps_bill"),

    # -- Professional Certification category --
    ("dps_cert",         "Professional Certification and Licensure",             1, None),
    ("dps_cert_cpa",     "CPA - Certified Public Accountant",                  2, "dps_cert"),
    ("dps_cert_jd",      "JD - Juris Doctor and Bar Admission",                2, "dps_cert"),
    ("dps_cert_pe",      "PE - Professional Engineer License",                 2, "dps_cert"),
    ("dps_cert_pmp",     "PMP - Project Management Professional",              2, "dps_cert"),
]

_DOMAIN_ROW = (
    "domain_prof_services",
    "Professional Services Types",
    "Service line, engagement type, billing model and certification taxonomy for NAICS 54",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["54"]


def _determine_level(code: str) -> int:
    """Return level: 1 for top categories, 2 for specific service types."""
    parts = code.split("_")
    if len(parts) == 2:
        return 1
    return 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_prof_services(conn) -> int:
    """Ingest Professional Services domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_prof_services'), and links NAICS 54xxx nodes
    via node_taxonomy_link.

    Returns total professional service node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_prof_services",
        "Professional Services Types",
        "Service line, engagement type, billing model and certification taxonomy for NAICS 54",
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

    parent_codes = {parent for _, _, _, parent in PROF_NODES if parent is not None}

    rows = [
        (
            "domain_prof_services",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in PROF_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(PROF_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_prof_services'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_prof_services'",
        count,
    )

    naics_codes = [
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE '54%'"
        )
    ]

    await conn.executemany(
        """INSERT INTO node_taxonomy_link
               (system_id, node_code, taxonomy_id, relevance)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
        [("naics_2022", code, "domain_prof_services", "primary") for code in naics_codes],
    )

    return count
