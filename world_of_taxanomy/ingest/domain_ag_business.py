"""Agricultural Farm Business Structure domain taxonomy ingester.

Classifies WHO owns and operates the farm - orthogonal to what crops are
grown, what animals are raised, what equipment is used, and what inputs
are applied. The same corn acre can be operated by a 4th-generation family
farm, a REIT-owned corporate farm, an agricultural cooperative, or a
contract grower tied to a food processor.

Code prefix: dab_
Categories: Farm Ownership Type, Farm Size and Scale, Business and Legal
Structure, Integration and Contracting Model, Capital and Financing Type.

Stakeholders: USDA Census of Agriculture, FSA program eligibility officers,
ag lenders (FCS, USDA RBCS), private equity ag investors, food processors
managing contract grower networks.
Source: USDA NASS Census of Agriculture, USDA ERS farm typology. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_BUSINESS_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Farm Ownership Type --
    ("dab_own",               "Farm Ownership Type",                                  1, None),
    ("dab_own_family",        "Family Farm (operator household owns and manages)",    2, "dab_own"),
    ("dab_own_coop",          "Agricultural Cooperative (member-owned)",              2, "dab_own"),
    ("dab_own_corporate",     "Corporate or Investor-Owned Farm (non-family)",        2, "dab_own"),
    ("dab_own_reit",          "Farmland REIT or Investment Fund",                     2, "dab_own"),
    ("dab_own_govt",          "Government or Tribal Land Farm",                       2, "dab_own"),

    # -- Farm Size and Scale --
    ("dab_size",              "Farm Size and Scale",                                   1, None),
    ("dab_size_small",        "Small Farm (under 180 acres / under $350k sales)",     2, "dab_size"),
    ("dab_size_mid",          "Mid-Size Farm (180-999 acres / $350k-$1M sales)",      2, "dab_size"),
    ("dab_size_large",        "Large Farm (1,000-4,999 acres / $1M-$5M sales)",       2, "dab_size"),
    ("dab_size_verylarge",    "Very Large Farm (5,000+ acres / over $5M sales)",      2, "dab_size"),

    # -- Business and Legal Structure --
    ("dab_structure",         "Business and Legal Structure",                          1, None),
    ("dab_structure_sole",    "Sole Proprietorship (individual farmer)",              2, "dab_structure"),
    ("dab_structure_partner", "Partnership (family or non-family general partner)",   2, "dab_structure"),
    ("dab_structure_llc",     "LLC or LLP (limited liability company)",               2, "dab_structure"),
    ("dab_structure_corp",    "C-Corp or S-Corp",                                     2, "dab_structure"),
    ("dab_structure_trust",   "Family Trust or Estate Operation",                     2, "dab_structure"),

    # -- Integration and Contracting Model --
    ("dab_contract",          "Integration and Contracting Model",                    1, None),
    ("dab_contract_grower",   "Contract Grower (production contract with integrator)", 2, "dab_contract"),
    ("dab_contract_vertical", "Vertically Integrated Operation (owns feed to meat)",  2, "dab_contract"),
    ("dab_contract_tenant",   "Tenant Farmer (cash rent or crop share lease)",        2, "dab_contract"),
    ("dab_contract_custom",   "Custom Farming Service (hired operator, owns land)",   2, "dab_contract"),

    # -- Capital and Financing Type --
    ("dab_capital",           "Capital and Financing Type",                            1, None),
    ("dab_capital_fcs",       "Farm Credit System (FCS) Borrower",                   2, "dab_capital"),
    ("dab_capital_usda",      "USDA FSA / RBCS Loan Program Participant",             2, "dab_capital"),
    ("dab_capital_bank",      "Commercial Bank Agricultural Loan",                    2, "dab_capital"),
    ("dab_capital_equity",    "Private Equity or Venture Capital Backed",             2, "dab_capital"),
]

_DOMAIN_ROW = (
    "domain_ag_business",
    "Agricultural Farm Business Structure Types",
    "Agricultural farm business structure classification - ownership type, "
    "farm size, legal structure, integration model, and capital type",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific business structure types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_business(conn) -> int:
    """Ingest Agricultural Farm Business Structure domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_business'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_business",
        "Agricultural Farm Business Structure Types",
        "Agricultural farm business structure classification - ownership type, "
        "farm size, legal structure, integration model, and capital type",
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

    parent_codes = {parent for _, _, _, parent in AG_BUSINESS_NODES if parent is not None}

    rows = [
        (
            "domain_ag_business",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_BUSINESS_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_BUSINESS_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_business'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_business'",
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
            [("naics_2022", code, "domain_ag_business", "primary") for code in naics_codes],
        )

    return count
