"""Public Administration Funding Mechanism Types domain taxonomy ingester.

Public administration funding mechanism classification - appropriations, tax revenue, fees, bonds, grants, intergovernmental transfers.

Code prefix: dpafund_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
PUBLIC_FUNDING_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Appropriations and Tax Revenue Funding --
    ("dpafund_approp", "Appropriations and Tax Revenue Funding", 1, None),
    ("dpafund_approp_annual", "Annual Appropriations (discretionary, mandatory budget)", 2, 'dpafund_approp'),
    ("dpafund_approp_capital", "Capital Appropriations and Infrastructure Funding", 2, 'dpafund_approp'),
    ("dpafund_approp_tax", "Property, Sales, and Income Tax Revenue", 2, 'dpafund_approp'),
    # -- User Fees and Regulatory Charges --
    ("dpafund_fees", "User Fees and Regulatory Charges", 1, None),
    ("dpafund_fees_user", "User Fees and Service Charges (utility, permit, license)", 2, 'dpafund_fees'),
    ("dpafund_fees_fine", "Fines, Penalties, and Forfeitures", 2, 'dpafund_fees'),
    ("dpafund_fees_franchise", "Franchise Fees and Right-of-Way Revenues", 2, 'dpafund_fees'),
    # -- Grant and Intergovernmental Funding --
    ("dpafund_grants", "Grant and Intergovernmental Funding", 1, None),
    ("dpafund_grants_federal", "Federal Grants and Formula Funding (CDBG, Title I, FHWA)", 2, 'dpafund_grants'),
    ("dpafund_grants_state", "State Aid and Pass-Through Grants to Local Government", 2, 'dpafund_grants'),
    ("dpafund_grants_foundation", "Foundation and Private Grant Funding (public entity)", 2, 'dpafund_grants'),
    # -- Debt and Bond Financing --
    ("dpafund_bonds", "Debt and Bond Financing", 1, None),
    ("dpafund_bonds_go", "General Obligation (GO) Bond (full faith and credit)", 2, 'dpafund_bonds'),
    ("dpafund_bonds_revenue", "Revenue Bond (pledged revenue stream - toll, utility)", 2, 'dpafund_bonds'),
    ("dpafund_bonds_tax", "Tax Increment Financing (TIF) and Special Assessment", 2, 'dpafund_bonds'),
    # -- Federal Direct Expenditure and Transfers --
    ("dpafund_federal", "Federal Direct Expenditure and Transfers", 1, None),
    ("dpafund_federal_entitlement", "Entitlement Programs (Medicare, Medicaid, Social Security)", 2, 'dpafund_federal'),
    ("dpafund_federal_direct", "Federal Direct Services and Operations Funding", 2, 'dpafund_federal'),
]

_DOMAIN_ROW = (
    "domain_public_funding",
    "Public Administration Funding Mechanism Types",
    "Public administration funding mechanism classification - appropriations, tax revenue, fees, bonds, grants, intergovernmental transfers",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['92']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_public_funding(conn) -> int:
    """Ingest Public Administration Funding Mechanism Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_public_funding",
        "Public Administration Funding Mechanism Types",
        "Public administration funding mechanism classification - appropriations, tax revenue, fees, bonds, grants, intergovernmental transfers",
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

    parent_codes = {parent for _, _, _, parent in PUBLIC_FUNDING_NODES if parent is not None}

    rows = [
        (
            "domain_public_funding",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in PUBLIC_FUNDING_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(PUBLIC_FUNDING_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_public_funding'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_public_funding'",
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
            [("naics_2022", code, "domain_public_funding", "primary") for code in naics_codes],
        )

    return count
