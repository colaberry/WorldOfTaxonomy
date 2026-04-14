"""Finance Regulatory Framework Types domain taxonomy ingester.

Finance regulatory framework classification - SEC, CFTC, banking regulators, state insurance, international.

Code prefix: dfireg_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
FINANCE_REGULATORY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- SEC Securities Regulation --
    ("dfireg_sec", "SEC Securities Regulation", 1, None),
    ("dfireg_sec_broker", "SEC Broker-Dealer Registration (15 USCA, FINRA)", 2, 'dfireg_sec'),
    ("dfireg_sec_ia", "SEC Investment Adviser Registration (Form ADV)", 2, 'dfireg_sec'),
    ("dfireg_sec_public", "SEC Public Reporting (10-K, 10-Q, 8-K filers)", 2, 'dfireg_sec'),
    # -- CFTC Derivatives Regulation --
    ("dfireg_cftc", "CFTC Derivatives Regulation", 1, None),
    ("dfireg_cftc_futures", "CFTC Futures Commission Merchant (FCM) Registration", 2, 'dfireg_cftc'),
    ("dfireg_cftc_swaps", "CFTC Swap Dealer and Major Swap Participant", 2, 'dfireg_cftc'),
    # -- Banking and Depository Institution Regulation --
    ("dfireg_banking", "Banking and Depository Institution Regulation", 1, None),
    ("dfireg_banking_fed", "Federal Reserve / BHC Supervision", 2, 'dfireg_banking'),
    ("dfireg_banking_occ", "OCC National Bank Charter Regulation", 2, 'dfireg_banking'),
    ("dfireg_banking_fdic", "FDIC Insured Depository Institution Supervision", 2, 'dfireg_banking'),
    # -- Insurance Regulation --
    ("dfireg_insurance", "Insurance Regulation", 1, None),
    ("dfireg_insurance_state", "State Insurance Department Licensing and Solvency", 2, 'dfireg_insurance'),
    ("dfireg_insurance_naic", "NAIC Model Laws and RBC (Risk-Based Capital)", 2, 'dfireg_insurance'),
    # -- International and Cross-Border Regulation --
    ("dfireg_intl", "International and Cross-Border Regulation", 1, None),
    ("dfireg_intl_basel", "Basel III/IV Bank Capital and Liquidity Standards", 2, 'dfireg_intl'),
    ("dfireg_intl_mifid", "MiFID II / EMIR European Markets Regulation", 2, 'dfireg_intl'),
    ("dfireg_intl_aml", "AML/KYC FATF Standards and Bank Secrecy Act", 2, 'dfireg_intl'),
]

_DOMAIN_ROW = (
    "domain_finance_regulatory",
    "Finance Regulatory Framework Types",
    "Finance regulatory framework classification - SEC, CFTC, banking regulators, state insurance, international",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['52']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_finance_regulatory(conn) -> int:
    """Ingest Finance Regulatory Framework Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_finance_regulatory",
        "Finance Regulatory Framework Types",
        "Finance regulatory framework classification - SEC, CFTC, banking regulators, state insurance, international",
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

    parent_codes = {parent for _, _, _, parent in FINANCE_REGULATORY_NODES if parent is not None}

    rows = [
        (
            "domain_finance_regulatory",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in FINANCE_REGULATORY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(FINANCE_REGULATORY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_finance_regulatory'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_finance_regulatory'",
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
            [("naics_2022", code, "domain_finance_regulatory", "primary") for code in naics_codes],
        )

    return count
