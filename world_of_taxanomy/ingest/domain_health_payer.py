"""Healthcare Payer and Reimbursement Model Types domain taxonomy ingester.

Healthcare payer and reimbursement model classification - Medicare, Medicaid, commercial, self-pay, value-based care.

Code prefix: dhspay_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
HEALTH_PAYER_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Medicare Program Reimbursement --
    ("dhspay_medicare", "Medicare Program Reimbursement", 1, None),
    ("dhspay_medicare_ffs", "Medicare Fee-for-Service (FFS) Part A/B/D", 2, 'dhspay_medicare'),
    ("dhspay_medicare_ma", "Medicare Advantage (MA / Part C - managed care)", 2, 'dhspay_medicare'),
    ("dhspay_medicare_apm", "Medicare APM (MSSP ACO, BPCI, direct contracting)", 2, 'dhspay_medicare'),
    # -- Medicaid and CHIP Reimbursement --
    ("dhspay_medicaid", "Medicaid and CHIP Reimbursement", 1, None),
    ("dhspay_medicaid_ffs", "Medicaid Fee-for-Service (state-administered)", 2, 'dhspay_medicaid'),
    ("dhspay_medicaid_mco", "Medicaid Managed Care Organization (MCO)", 2, 'dhspay_medicaid'),
    # -- Commercial Insurance Reimbursement --
    ("dhspay_commercial", "Commercial Insurance Reimbursement", 1, None),
    ("dhspay_commercial_hmo", "Commercial HMO (capitation, gated referral)", 2, 'dhspay_commercial'),
    ("dhspay_commercial_ppo", "Commercial PPO (negotiated fee schedule)", 2, 'dhspay_commercial'),
    ("dhspay_commercial_hdhp", "High-Deductible Health Plan (HDHP) with HSA", 2, 'dhspay_commercial'),
    # -- Self-Pay and Uninsured --
    ("dhspay_selfpay", "Self-Pay and Uninsured", 1, None),
    ("dhspay_selfpay_cash", "Cash Pay and Direct Pay Primary Care (DPC)", 2, 'dhspay_selfpay'),
    ("dhspay_selfpay_charity", "Charity Care and Uncompensated Care", 2, 'dhspay_selfpay'),
    # -- Value-Based Care and Risk Arrangements --
    ("dhspay_vbc", "Value-Based Care and Risk Arrangements", 1, None),
    ("dhspay_vbc_bundle", "Episode-Based / Bundled Payment (CJR, BPCI)", 2, 'dhspay_vbc'),
    ("dhspay_vbc_shared", "Shared Savings (ACO, upside-only, two-sided risk)", 2, 'dhspay_vbc'),
    ("dhspay_vbc_cap", "Global Capitation (PMPM - full risk, prepaid)", 2, 'dhspay_vbc'),
]

_DOMAIN_ROW = (
    "domain_health_payer",
    "Healthcare Payer and Reimbursement Model Types",
    "Healthcare payer and reimbursement model classification - Medicare, Medicaid, commercial, self-pay, value-based care",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['62']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_health_payer(conn) -> int:
    """Ingest Healthcare Payer and Reimbursement Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_health_payer",
        "Healthcare Payer and Reimbursement Model Types",
        "Healthcare payer and reimbursement model classification - Medicare, Medicaid, commercial, self-pay, value-based care",
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

    parent_codes = {parent for _, _, _, parent in HEALTH_PAYER_NODES if parent is not None}

    rows = [
        (
            "domain_health_payer",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in HEALTH_PAYER_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(HEALTH_PAYER_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_health_payer'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_health_payer'",
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
            [("naics_2022", code, "domain_health_payer", "primary") for code in naics_codes],
        )

    return count
