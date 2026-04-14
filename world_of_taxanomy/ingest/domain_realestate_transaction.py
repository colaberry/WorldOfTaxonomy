"""Real Estate Transaction Type Classification domain taxonomy ingester.

Real estate transaction type classification - acquisition, development, refinancing, disposition, recapitalization.

Code prefix: drttxn_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
RE_TRANSACTION_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Acquisition and Investment --
    ("drttxn_acquire", "Acquisition and Investment", 1, None),
    ("drttxn_acquire_core", "Core Acquisition (stabilized, low risk, low return)", 2, 'drttxn_acquire'),
    ("drttxn_acquire_value", "Value-Add Acquisition (repositioning, renovation)", 2, 'drttxn_acquire'),
    ("drttxn_acquire_opp", "Opportunistic Acquisition (distressed, development site)", 2, 'drttxn_acquire'),
    # -- Development and Construction --
    ("drttxn_develop", "Development and Construction", 1, None),
    ("drttxn_develop_ground", "Ground-Up Development (new construction from land)", 2, 'drttxn_develop'),
    ("drttxn_develop_adaptive", "Adaptive Reuse (office to residential, historic conversion)", 2, 'drttxn_develop'),
    ("drttxn_develop_condo", "Condominium Conversion and Subdivision", 2, 'drttxn_develop'),
    # -- Financing and Capital Transaction --
    ("drttxn_finance", "Financing and Capital Transaction", 1, None),
    ("drttxn_finance_refi", "Refinancing (rate/term, cash-out, construction perm)", 2, 'drttxn_finance'),
    ("drttxn_finance_mezz", "Mezzanine and Preferred Equity Placement", 2, 'drttxn_finance'),
    ("drttxn_finance_cmbs", "CMBS and Agency (Fannie, Freddie, HUD) Financing", 2, 'drttxn_finance'),
    # -- Disposition and Exit --
    ("drttxn_dispose", "Disposition and Exit", 1, None),
    ("drttxn_dispose_sale", "Outright Sale (broker marketed, off-market)", 2, 'drttxn_dispose'),
    ("drttxn_dispose_1031", "1031 Like-Kind Exchange Transaction", 2, 'drttxn_dispose'),
    ("drttxn_dispose_recap", "Recapitalization (partial interest sale, JV recap)", 2, 'drttxn_dispose'),
]

_DOMAIN_ROW = (
    "domain_realestate_transaction",
    "Real Estate Transaction Type Classification",
    "Real estate transaction type classification - acquisition, development, refinancing, disposition, recapitalization",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['53']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_realestate_transaction(conn) -> int:
    """Ingest Real Estate Transaction Type Classification.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_realestate_transaction",
        "Real Estate Transaction Type Classification",
        "Real estate transaction type classification - acquisition, development, refinancing, disposition, recapitalization",
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

    parent_codes = {parent for _, _, _, parent in RE_TRANSACTION_NODES if parent is not None}

    rows = [
        (
            "domain_realestate_transaction",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in RE_TRANSACTION_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(RE_TRANSACTION_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_realestate_transaction'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_realestate_transaction'",
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
            [("naics_2022", code, "domain_realestate_transaction", "primary") for code in naics_codes],
        )

    return count
