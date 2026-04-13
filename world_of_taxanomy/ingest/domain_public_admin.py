"""Public Administration domain taxonomy ingester.

Public administration taxonomy organizes government functions (NAICS 92):
  Government Level  (dpa_level*)  - federal, state, local, tribal, special district
  Government Function (dpa_func*) - defense, justice, revenue, social services, infrastructure
  Agency Type       (dpa_agency*) - executive, legislative, judicial, independent, quasi-govt
  Government Process (dpa_proc*)  - rulemaking, procurement, adjudication, elections

Source: NAICS 92 subsectors + COFOG (UN Classification of Functions of Government).
Public domain. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
PUBLIC_ADMIN_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Government Level category --
    ("dpa_level",          "Government Level",                                   1, None),
    ("dpa_level_federal",  "Federal and National Government",                  2, "dpa_level"),
    ("dpa_level_state",    "State and Provincial Government",                  2, "dpa_level"),
    ("dpa_level_local",    "Local, County and Municipal Government",           2, "dpa_level"),
    ("dpa_level_tribal",   "Tribal and Indigenous Government",                 2, "dpa_level"),
    ("dpa_level_special",  "Special District (water, transit, school district)",2, "dpa_level"),

    # -- Government Function category --
    ("dpa_func",           "Government Function Type",                           1, None),
    ("dpa_func_defense",   "Defense and National Security",                    2, "dpa_func"),
    ("dpa_func_justice",   "Justice, Public Safety and Courts",                2, "dpa_func"),
    ("dpa_func_revenue",   "Tax Collection and Revenue Administration",        2, "dpa_func"),
    ("dpa_func_social",    "Social Services and Public Welfare",               2, "dpa_func"),
    ("dpa_func_infra",     "Infrastructure, Transportation and Public Works",  2, "dpa_func"),
    ("dpa_func_env",       "Environment, Natural Resources and Land Use",      2, "dpa_func"),

    # -- Agency Type category --
    ("dpa_agency",         "Agency and Entity Type",                             1, None),
    ("dpa_agency_exec",    "Executive Department or Cabinet Agency",           2, "dpa_agency"),
    ("dpa_agency_legis",   "Legislative Branch and Congress",                  2, "dpa_agency"),
    ("dpa_agency_judic",   "Judicial Branch and Courts",                       2, "dpa_agency"),
    ("dpa_agency_indep",   "Independent Regulatory Agency (FCC, SEC, EPA)",   2, "dpa_agency"),

    # -- Government Process category --
    ("dpa_proc",             "Government Process Type",                          1, None),
    ("dpa_proc_rulemaking",  "Regulatory and Rulemaking Process",              2, "dpa_proc"),
    ("dpa_proc_procure",     "Government Procurement and Contracting",         2, "dpa_proc"),
    ("dpa_proc_adjudicate",  "Adjudication and Administrative Hearings",       2, "dpa_proc"),
    ("dpa_proc_elections",   "Elections, Voting and Electoral Administration", 2, "dpa_proc"),
]

_DOMAIN_ROW = (
    "domain_public_admin",
    "Public Administration Types",
    "Government level, function, agency type and process taxonomy for NAICS 92 public administration",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["92"]


def _determine_level(code: str) -> int:
    """Return level: 1 for top categories, 2 for specific government types."""
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


async def ingest_domain_public_admin(conn) -> int:
    """Ingest Public Administration domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_public_admin'), and links NAICS 92xxx nodes
    via node_taxonomy_link.

    Returns total public administration node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_public_admin",
        "Public Administration Types",
        "Government level, function, agency type and process taxonomy for NAICS 92 public administration",
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

    parent_codes = {parent for _, _, _, parent in PUBLIC_ADMIN_NODES if parent is not None}

    rows = [
        (
            "domain_public_admin",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in PUBLIC_ADMIN_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(PUBLIC_ADMIN_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_public_admin'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_public_admin'",
        count,
    )

    naics_codes = [
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE '92%'"
        )
    ]

    await conn.executemany(
        """INSERT INTO node_taxonomy_link
               (system_id, node_code, taxonomy_id, relevance)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
        [("naics_2022", code, "domain_public_admin", "primary") for code in naics_codes],
    )

    return count
