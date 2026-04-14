"""Mining Safety and Regulatory Compliance domain taxonomy ingester.

Classifies compliance frameworks - orthogonal to mineral type, extraction
method, reserve classification, equipment, and lifecycle phase. A surface
gold mine and an underground coal mine both face MSHA jurisdiction but
under completely different parts of 30 CFR, with different ventilation,
blasting, and ground control requirements.

Code prefix: dmsaf_
Categories: MSHA Regulatory Domain (US federal), Environmental and Water
Compliance, Tailings and Waste Management, International Safety Standards,
Community and Social License.

Stakeholders: mine safety officers, MSHA district offices, mine inspectors,
environmental compliance managers, ESG-focused investors tracking incident
rates, government bond administrators requiring reclamation assurance.
Source: MSHA 30 CFR Parts 46-100 (surface) and Parts 56-57 (underground),
EPA hard rock mining regulations, MAC Towards Sustainable Mining (TSM),
ICMM Mining Principles. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MINING_SAFETY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- MSHA Regulatory Domain --
    ("dmsaf_msha",            "MSHA Regulatory Domain (US - 30 CFR)",          1, None),
    ("dmsaf_msha_surface",    "MSHA Surface Metal/Non-Metal (30 CFR Part 56)", 2, "dmsaf_msha"),
    ("dmsaf_msha_underground","MSHA Underground Metal/Non-Metal (30 CFR 57)", 2, "dmsaf_msha"),
    ("dmsaf_msha_coal",       "MSHA Coal Mine Safety (30 CFR Parts 70-90)",   2, "dmsaf_msha"),
    ("dmsaf_msha_training",   "MSHA Miner Training (30 CFR Part 46/48)",      2, "dmsaf_msha"),

    # -- Environmental and Water Compliance --
    ("dmsaf_env",             "Environmental and Water Compliance",             1, None),
    ("dmsaf_env_water",       "Clean Water Act NPDES Stormwater Permit",       2, "dmsaf_env"),
    ("dmsaf_env_air",         "Clean Air Act Permit to Construct/Operate",     2, "dmsaf_env"),
    ("dmsaf_env_nepa",        "NEPA Environmental Impact Assessment (EIS/EA)", 2, "dmsaf_env"),
    ("dmsaf_env_superfund",   "CERCLA / Superfund Liability Management",       2, "dmsaf_env"),
    ("dmsaf_env_smcra",       "SMCRA Surface Mining Reclamation (coal)",       2, "dmsaf_env"),

    # -- Tailings and Waste Management --
    ("dmsaf_tailings",        "Tailings and Waste Management",                  1, None),
    ("dmsaf_tailings_dam",    "Tailings Storage Facility (TSF) - Dam Safety",  2, "dmsaf_tailings"),
    ("dmsaf_tailings_mac",    "MAC GISTM - Global Standard on TSF Management", 2, "dmsaf_tailings"),
    ("dmsaf_tailings_heap",   "Heap Leach Pad Liner and Containment System",  2, "dmsaf_tailings"),
    ("dmsaf_tailings_waste",  "Waste Rock Dump and Acid Rock Drainage (ARD)", 2, "dmsaf_tailings"),

    # -- International Safety Standards --
    ("dmsaf_intl",            "International Safety and ESG Standards",         1, None),
    ("dmsaf_intl_icmm",       "ICMM Mining Principles (10 principles, 6 WDs)", 2, "dmsaf_intl"),
    ("dmsaf_intl_tsm",        "MAC Towards Sustainable Mining (TSM) Protocol", 2, "dmsaf_intl"),
    ("dmsaf_intl_ifc",        "IFC Performance Standards on Mining",           2, "dmsaf_intl"),
    ("dmsaf_intl_eiti",       "EITI Extractive Industries Transparency Reporting", 2, "dmsaf_intl"),

    # -- Community and Social License --
    ("dmsaf_social",          "Community and Social License to Operate",        1, None),
    ("dmsaf_social_fpic",     "Free, Prior, and Informed Consent (FPIC)",      2, "dmsaf_social"),
    ("dmsaf_social_iam",      "Indigenous and Aboriginal Community Agreement", 2, "dmsaf_social"),
    ("dmsaf_social_gm",       "Grievance Mechanism and Community Relations",   2, "dmsaf_social"),
]

_DOMAIN_ROW = (
    "domain_mining_safety",
    "Mining Safety and Regulatory Compliance Types",
    "Mining safety and regulatory compliance classification - MSHA, environmental, "
    "tailings management, international standards, and social license",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["21"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific safety/regulatory types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_mining_safety(conn) -> int:
    """Ingest Mining Safety and Regulatory Compliance domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_mining_safety'), and links NAICS 21 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_mining_safety",
        "Mining Safety and Regulatory Compliance Types",
        "Mining safety and regulatory compliance classification - MSHA, environmental, "
        "tailings management, international standards, and social license",
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

    parent_codes = {parent for _, _, _, parent in MINING_SAFETY_NODES if parent is not None}

    rows = [
        (
            "domain_mining_safety",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MINING_SAFETY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MINING_SAFETY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_mining_safety'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_mining_safety'",
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
            [("naics_2022", code, "domain_mining_safety", "primary") for code in naics_codes],
        )

    return count
