"""Utility Regulatory Framework domain taxonomy ingester.

Classifies what regulatory regime governs a utility - orthogonal to energy
source, grid region, tariff structure, and asset type. An investor-owned
utility (IOU) serving the same load that a rural electric cooperative or a
municipal utility serves operates under completely different regulatory
frameworks, ratemaking processes, and ownership structures.

Code prefix: dureg_
Categories: Ownership and Utility Type, Federal Regulatory Jurisdiction,
State and Provincial Regulation, Market Structure and Competition,
Environmental Regulation.

Stakeholders: utility regulatory attorneys, state PUC commissioners, FERC
staff, rural electric cooperative (REC) directors, municipal utility managers,
energy policy analysts.
Source: FERC jurisdiction statutes (FPA, NGA), NARUC state commission
classifications, NRECA cooperative utility standards, EIA Form 861. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
UTIL_REGULATORY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Ownership and Utility Type --
    ("dureg_own",             "Ownership and Utility Type",                     1, None),
    ("dureg_own_iou",         "Investor-Owned Utility (IOU) - state-regulated", 2, "dureg_own"),
    ("dureg_own_muni",        "Municipal Utility (publicly owned, home rule)",  2, "dureg_own"),
    ("dureg_own_coop",        "Rural Electric Cooperative (REC - member-owned)", 2, "dureg_own"),
    ("dureg_own_fed",         "Federal Power Marketing Administration (Bonneville, TVA)", 2, "dureg_own"),
    ("dureg_own_nonutility",  "Non-Utility Generator / Independent Power Producer", 2, "dureg_own"),

    # -- Federal Regulatory Jurisdiction --
    ("dureg_federal",         "Federal Regulatory Jurisdiction",                 1, None),
    ("dureg_federal_ferc",    "FERC Electric (FPA Section 205/206 tariff review)", 2, "dureg_federal"),
    ("dureg_federal_ferc_gas","FERC Natural Gas (NGA Section 4/5 rate regulation)", 2, "dureg_federal"),
    ("dureg_federal_nerc",    "NERC Reliability Standards (CIP, FAC, PRC, TPL)", 2, "dureg_federal"),
    ("dureg_federal_rto",     "ISO/RTO Market Rules (PJM, MISO, CAISO, ISO-NE)", 2, "dureg_federal"),

    # -- State and Provincial Regulation --
    ("dureg_state",           "State and Provincial Regulation",                 1, None),
    ("dureg_state_puc",       "State Public Utility Commission (PUC/PSC) Rate Case", 2, "dureg_state"),
    ("dureg_state_rps",       "Renewable Portfolio Standard (RPS) Compliance",  2, "dureg_state"),
    ("dureg_state_iou_gas",   "State Gas Distribution Regulation",              2, "dureg_state"),
    ("dureg_state_exempt",    "Exempt Wholesale Generator (EWG) Status",        2, "dureg_state"),

    # -- Market Structure and Competition --
    ("dureg_market",          "Market Structure and Competition Framework",      1, None),
    ("dureg_market_vertint",  "Vertically Integrated Utility (regulated monopoly)", 2, "dureg_market"),
    ("dureg_market_deregulated","Deregulated / Restructured Market (retail choice)", 2, "dureg_market"),
    ("dureg_market_hybrid",   "Hybrid Market (regulated wires, competitive supply)", 2, "dureg_market"),

    # -- Environmental Regulation --
    ("dureg_env",             "Environmental Regulatory Framework",              1, None),
    ("dureg_env_caa",         "Clean Air Act Permitting (Title IV, Title V)",   2, "dureg_env"),
    ("dureg_env_ghg",         "GHG Reporting and Carbon Market Compliance",     2, "dureg_env"),
    ("dureg_env_effluent",    "Clean Water Act Effluent Limitations (316(b))",  2, "dureg_env"),
    ("dureg_env_ccr",         "Coal Combustion Residuals (CCR) Rule Compliance", 2, "dureg_env"),
]

_DOMAIN_ROW = (
    "domain_util_regulatory",
    "Utility Regulatory Framework Types",
    "Utility regulatory framework classification - ownership type, federal, state, "
    "market structure, and environmental regulatory compliance",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["22"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific regulatory framework types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_util_regulatory(conn) -> int:
    """Ingest Utility Regulatory Framework domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_util_regulatory'), and links NAICS 22 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_util_regulatory",
        "Utility Regulatory Framework Types",
        "Utility regulatory framework classification - ownership type, federal, state, "
        "market structure, and environmental regulatory compliance",
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

    parent_codes = {parent for _, _, _, parent in UTIL_REGULATORY_NODES if parent is not None}

    rows = [
        (
            "domain_util_regulatory",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in UTIL_REGULATORY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(UTIL_REGULATORY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_util_regulatory'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_util_regulatory'",
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
            [("naics_2022", code, "domain_util_regulatory", "primary") for code in naics_codes],
        )

    return count
