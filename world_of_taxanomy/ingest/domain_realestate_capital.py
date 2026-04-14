"""Real Estate Capital Structure and Ownership Vehicle Types domain taxonomy ingester.

Real estate capital structure and ownership vehicle classification - REIT, fund, syndication, DST, direct ownership.

Code prefix: drtcap_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
RE_CAPITAL_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Real Estate Investment Trust (REIT) --
    ("drtcap_reit", "Real Estate Investment Trust (REIT)", 1, None),
    ("drtcap_reit_equity", "Equity REIT (owns income-producing properties)", 2, 'drtcap_reit'),
    ("drtcap_reit_mortgage", "Mortgage REIT (mREIT - holds real estate debt)", 2, 'drtcap_reit'),
    ("drtcap_reit_public", "Publicly Traded REIT (NYSE, NASDAQ listed)", 2, 'drtcap_reit'),
    # -- Private Real Estate Fund Structure --
    ("drtcap_fund", "Private Real Estate Fund Structure", 1, None),
    ("drtcap_fund_closedend", "Closed-End Commingled Real Estate Fund", 2, 'drtcap_fund'),
    ("drtcap_fund_openend", "Open-End Core Fund (evergreen, quarterly redemption)", 2, 'drtcap_fund'),
    ("drtcap_fund_sep", "Separate Account (institutional, pension, SWF)", 2, 'drtcap_fund'),
    # -- Syndication and Fractional Ownership --
    ("drtcap_syndication", "Syndication and Fractional Ownership", 1, None),
    ("drtcap_syndication_506b", "Reg D 506(b) Syndication (accredited investors)", 2, 'drtcap_syndication'),
    ("drtcap_syndication_cf", "Regulation Crowdfunding (Reg CF, retail investors)", 2, 'drtcap_syndication'),
    ("drtcap_syndication_dst", "Delaware Statutory Trust (DST - 1031 exchange vehicle)", 2, 'drtcap_syndication'),
    # -- Direct and Owner-Operator Structures --
    ("drtcap_direct", "Direct and Owner-Operator Structures", 1, None),
    ("drtcap_direct_llc", "Single-Purpose LLC or LP (direct ownership entity)", 2, 'drtcap_direct'),
    ("drtcap_direct_jv", "Joint Venture (JV - developer plus capital partner)", 2, 'drtcap_direct'),
]

_DOMAIN_ROW = (
    "domain_realestate_capital",
    "Real Estate Capital Structure and Ownership Vehicle Types",
    "Real estate capital structure and ownership vehicle classification - REIT, fund, syndication, DST, direct ownership",
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


async def ingest_domain_realestate_capital(conn) -> int:
    """Ingest Real Estate Capital Structure and Ownership Vehicle Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_realestate_capital",
        "Real Estate Capital Structure and Ownership Vehicle Types",
        "Real estate capital structure and ownership vehicle classification - REIT, fund, syndication, DST, direct ownership",
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

    parent_codes = {parent for _, _, _, parent in RE_CAPITAL_NODES if parent is not None}

    rows = [
        (
            "domain_realestate_capital",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in RE_CAPITAL_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(RE_CAPITAL_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_realestate_capital'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_realestate_capital'",
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
            [("naics_2022", code, "domain_realestate_capital", "primary") for code in naics_codes],
        )

    return count
