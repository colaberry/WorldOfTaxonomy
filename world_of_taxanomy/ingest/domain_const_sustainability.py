"""Construction Sustainability and Green Building Certification domain taxonomy ingester.

Classifies what environmental performance certification and green building
standard applies to a project - orthogonal to trade type, building type,
delivery method, and material. The same LEED rating system certifies a
wood-frame affordable housing project, a concrete office tower, and a steel
data center, all using different delivery methods and trades.

Code prefix: dcss_
Categories: LEED and Green Building Rating Systems, Energy Performance
Certification, Embodied Carbon and Materials, Resilience and Climate
Adaptation, Green Financing and Incentive Programs.

Stakeholders: sustainability consultants, LEED APs, energy code officials
(ASHRAE 90.1), green bond issuers, ESG-focused real estate investors,
building owners seeking utility incentive rebates.
Source: USGBC LEED v4.1 rating system, ASHRAE 90.1 energy standard,
BREEAM standards, Passive House Institute PHI, IgCC. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
CONST_SUSTAINABILITY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- LEED and Green Building Rating Systems --
    ("dcss_leed",             "LEED and Green Building Rating Systems",          1, None),
    ("dcss_leed_bdnc",        "LEED BD+C (Building Design and Construction)",   2, "dcss_leed"),
    ("dcss_leed_id",          "LEED ID+C (Interior Design and Construction)",   2, "dcss_leed"),
    ("dcss_leed_om",          "LEED O+M (Operations and Maintenance)",          2, "dcss_leed"),
    ("dcss_leed_breeam",      "BREEAM (Building Research Establishment, UK/intl)", 2, "dcss_leed"),
    ("dcss_leed_green_globes","Green Globes (North American rating system)",    2, "dcss_leed"),

    # -- Energy Performance Certification --
    ("dcss_energy",           "Energy Performance Certification",                1, None),
    ("dcss_energy_energy_star","ENERGY STAR Certification (EPA, commercial bldg)", 2, "dcss_energy"),
    ("dcss_energy_ashrae",    "ASHRAE 90.1 Advanced Energy Design Guide",       2, "dcss_energy"),
    ("dcss_energy_passive",   "Passive House (PHI Certified, PHIUS+)",          2, "dcss_energy"),
    ("dcss_energy_zne",       "Zero Net Energy (ZNE) and Net Zero Carbon",      2, "dcss_energy"),

    # -- Embodied Carbon and Materials --
    ("dcss_carbon",           "Embodied Carbon and Material Health",             1, None),
    ("dcss_carbon_lca",       "Life Cycle Assessment (LCA - ISO 14040/44)",     2, "dcss_carbon"),
    ("dcss_carbon_epd",       "Environmental Product Declaration (EPD - PCR)",  2, "dcss_carbon"),
    ("dcss_carbon_declare",   "Declare and Chemicals of Concern Disclosure",    2, "dcss_carbon"),
    ("dcss_carbon_living",    "Living Building Challenge (LBC - regenerative)", 2, "dcss_carbon"),

    # -- Resilience and Climate Adaptation --
    ("dcss_resilience",       "Resilience and Climate Adaptation Standards",     1, None),
    ("dcss_resilience_fortified","IBHS FORTIFIED Construction Standard",        2, "dcss_resilience"),
    ("dcss_resilience_reset", "RESET Building Performance Standard",            2, "dcss_resilience"),
    ("dcss_resilience_well",  "WELL Building Standard (health and wellness)",   2, "dcss_resilience"),

    # -- Green Financing and Incentive Programs --
    ("dcss_finance",          "Green Financing and Incentive Programs",          1, None),
    ("dcss_finance_bond",     "Green Bond and Sustainability-Linked Loan",      2, "dcss_finance"),
    ("dcss_finance_ira",      "IRA Clean Energy Tax Credit (179D, 45L, 48C)",   2, "dcss_finance"),
    ("dcss_finance_rebate",   "Utility Rebate and Incentive Program",           2, "dcss_finance"),
]

_DOMAIN_ROW = (
    "domain_const_sustainability",
    "Construction Sustainability and Green Building Types",
    "Construction sustainability and green building certification - LEED, energy "
    "performance, embodied carbon, resilience, and green financing",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["23"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific sustainability certification types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_const_sustainability(conn) -> int:
    """Ingest Construction Sustainability and Green Building domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_const_sustainability'), and links NAICS 23 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_const_sustainability",
        "Construction Sustainability and Green Building Types",
        "Construction sustainability and green building certification - LEED, energy "
        "performance, embodied carbon, resilience, and green financing",
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

    parent_codes = {parent for _, _, _, parent in CONST_SUSTAINABILITY_NODES if parent is not None}

    rows = [
        (
            "domain_const_sustainability",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in CONST_SUSTAINABILITY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(CONST_SUSTAINABILITY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_const_sustainability'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_const_sustainability'",
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
            [("naics_2022", code, "domain_const_sustainability", "primary") for code in naics_codes],
        )

    return count
