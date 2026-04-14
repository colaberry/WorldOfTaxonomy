"""Agricultural Regulatory and Compliance Framework domain taxonomy ingester.

Classifies compliance frameworks - orthogonal to crop type, farming method,
equipment, inputs, and market channel. The same produce can be subject to
USDA grading, FDA FSMA traceability, organic certification, and GlobalGAP
simultaneously, each managed by different regulators, auditors, and buyers.

Code prefix: dagr_
Categories: USDA Commodity Program Compliance, FDA Food Safety (FSMA),
Organic and Sustainability Certification, Export and Phytosanitary,
Environmental Compliance, Labor and Worker Protection.

Stakeholders: compliance managers, export certifiers, organic certifiers,
food retailers requiring supplier certifications, crop insurance adjusters.
Source: USDA AMS/FSIS/FSA regulations, FDA FSMA rules, USDA NOP, APHIS PPQ
phytosanitary programs, EPA FIFRA. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_REGULATORY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- USDA Commodity Program Compliance --
    ("dagr_usda",             "USDA Commodity Program Compliance",                    1, None),
    ("dagr_usda_fsa",         "FSA Farm Program (ARC, PLC, CRP enrollment)",         2, "dagr_usda"),
    ("dagr_usda_nrcs",        "NRCS Conservation Program (EQIP, CSP compliance)",    2, "dagr_usda"),
    ("dagr_usda_crop_ins",    "USDA Crop Insurance (FCIC/RMA policy requirements)",  2, "dagr_usda"),
    ("dagr_usda_grade",       "USDA Agricultural Marketing and Grading Standards",   2, "dagr_usda"),

    # -- FDA Food Safety (FSMA) --
    ("dagr_fsma",             "FDA Food Safety (FSMA) Compliance",                   1, None),
    ("dagr_fsma_produce",     "FSMA Produce Safety Rule (PSR) - 21 CFR Part 112",   2, "dagr_fsma"),
    ("dagr_fsma_pchf",        "FSMA PCHF Rule (human food preventive controls)",    2, "dagr_fsma"),
    ("dagr_fsma_fsvp",        "FSMA Foreign Supplier Verification Program (FSVP)",  2, "dagr_fsma"),
    ("dagr_fsma_204",         "FSMA Section 204 Traceability Rule (HFT foods)",     2, "dagr_fsma"),

    # -- Organic and Sustainability Certification --
    ("dagr_organic",          "Organic and Sustainability Certification",             1, None),
    ("dagr_organic_nop",      "USDA National Organic Program (NOP) Certification",  2, "dagr_organic"),
    ("dagr_organic_trans",    "Transitional Organic (3-year NOP transition period)", 2, "dagr_organic"),
    ("dagr_organic_global",   "International Organic Equivalency (EU, JAS, CAAQ)",  2, "dagr_organic"),
    ("dagr_organic_regener",  "Regenerative Agriculture Certification (ROC, REOC)", 2, "dagr_organic"),
    ("dagr_organic_gap",      "GlobalGAP and Good Agricultural Practices (GAP)",    2, "dagr_organic"),

    # -- Export and Phytosanitary --
    ("dagr_export",           "Export and Phytosanitary Compliance",                  1, None),
    ("dagr_export_pq",        "USDA APHIS PPQ Phytosanitary Certificate",            2, "dagr_export"),
    ("dagr_export_fsis",      "USDA FSIS Export Meat and Poultry Certificate",       2, "dagr_export"),
    ("dagr_export_eu",        "EU Third-Country Establishment Listing",              2, "dagr_export"),
    ("dagr_export_china",     "China GACC (General Administration of Customs) Reg", 2, "dagr_export"),

    # -- Environmental Compliance --
    ("dagr_env",              "Environmental Compliance",                              1, None),
    ("dagr_env_cafo",         "CAFO NPDES Permit (concentrated animal feeding ops)", 2, "dagr_env"),
    ("dagr_env_wetland",      "Wetland Conservation and Swampbuster Compliance",     2, "dagr_env"),
    ("dagr_env_pest",         "EPA FIFRA Pesticide Applicator License",              2, "dagr_env"),
    ("dagr_env_carbon",       "Carbon Credit Program Registration (VCS, ACR, Gold)", 2, "dagr_env"),

    # -- Labor and Worker Protection --
    ("dagr_labor",            "Labor and Worker Protection Standards",                1, None),
    ("dagr_labor_h2a",        "H-2A Agricultural Worker Visa Program Compliance",    2, "dagr_labor"),
    ("dagr_labor_wps",        "EPA Worker Protection Standard (WPS) for Pesticides", 2, "dagr_labor"),
    ("dagr_labor_osha",       "OSHA Agricultural Safety Standards",                  2, "dagr_labor"),
]

_DOMAIN_ROW = (
    "domain_ag_regulatory",
    "Agricultural Regulatory Compliance Types",
    "Agricultural regulatory and compliance framework classification - USDA programs, "
    "FDA FSMA, organic certification, export, environmental, and labor compliance",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific regulatory framework types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_regulatory(conn) -> int:
    """Ingest Agricultural Regulatory Compliance domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_regulatory'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_regulatory",
        "Agricultural Regulatory Compliance Types",
        "Agricultural regulatory and compliance framework classification - USDA programs, "
        "FDA FSMA, organic certification, export, environmental, and labor compliance",
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

    parent_codes = {parent for _, _, _, parent in AG_REGULATORY_NODES if parent is not None}

    rows = [
        (
            "domain_ag_regulatory",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_REGULATORY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_REGULATORY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_regulatory'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_regulatory'",
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
            [("naics_2022", code, "domain_ag_regulatory", "primary") for code in naics_codes],
        )

    return count
