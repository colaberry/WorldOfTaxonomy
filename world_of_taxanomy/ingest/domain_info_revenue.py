"""Information and Media Revenue and Monetization Model Types domain taxonomy ingester.

Information and media revenue model classification - subscription, advertising, transactional, licensing, patronage.

Code prefix: dimrev_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
INFO_REVENUE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Subscription and Membership Revenue Models --
    ("dimrev_subscription", "Subscription and Membership Revenue Models", 1, None),
    ("dimrev_subscription_svod", "SVOD (Subscription Video On Demand - Netflix, Disney+)", 2, 'dimrev_subscription'),
    ("dimrev_subscription_saas", "SaaS Subscription (cloud software, monthly/annual)", 2, 'dimrev_subscription'),
    ("dimrev_subscription_news", "Digital News and Content Subscription (paywall)", 2, 'dimrev_subscription'),
    # -- Advertising and Sponsored Content Revenue Models --
    ("dimrev_advertising", "Advertising and Sponsored Content Revenue Models", 1, None),
    ("dimrev_advertising_programmatic", "Programmatic Advertising (DSP/SSP, RTB, audience targeting)", 2, 'dimrev_advertising'),
    ("dimrev_advertising_brand", "Brand / Direct Advertising (sponsorships, upfront buys)", 2, 'dimrev_advertising'),
    ("dimrev_advertising_search", "Search and Performance Advertising (CPC, CPA)", 2, 'dimrev_advertising'),
    # -- Transactional and Pay-Per-Use Revenue Models --
    ("dimrev_transactional", "Transactional and Pay-Per-Use Revenue Models", 1, None),
    ("dimrev_transactional_pvod", "PVOD / TVOD (Transactional Video - digital rental/purchase)", 2, 'dimrev_transactional'),
    ("dimrev_transactional_marketplace", "Marketplace Commission and Take Rate", 2, 'dimrev_transactional'),
    # -- Licensing and Syndication Revenue Models --
    ("dimrev_licensing", "Licensing and Syndication Revenue Models", 1, None),
    ("dimrev_licensing_ip", "IP and Content Licensing (royalties, sync fees)", 2, 'dimrev_licensing'),
    ("dimrev_licensing_api", "API and Data Licensing (Bloomberg, Refinitiv tiers)", 2, 'dimrev_licensing'),
    # -- Patronage, Grants, and Hybrid Models --
    ("dimrev_patronage", "Patronage, Grants, and Hybrid Models", 1, None),
    ("dimrev_patronage_npo", "Non-Profit Media and Grant-Funded (PBS, NPR, local news)", 2, 'dimrev_patronage'),
    ("dimrev_patronage_creator", "Creator Economy (Patreon, Substack, crowdfunding)", 2, 'dimrev_patronage'),
    ("dimrev_patronage_philanthropy", "Philanthropic and Foundation-Funded Media", 2, 'dimrev_patronage'),
]

_DOMAIN_ROW = (
    "domain_info_revenue",
    "Information and Media Revenue and Monetization Model Types",
    "Information and media revenue model classification - subscription, advertising, transactional, licensing, patronage",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['51']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_info_revenue(conn) -> int:
    """Ingest Information and Media Revenue and Monetization Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_info_revenue",
        "Information and Media Revenue and Monetization Model Types",
        "Information and media revenue model classification - subscription, advertising, transactional, licensing, patronage",
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

    parent_codes = {parent for _, _, _, parent in INFO_REVENUE_NODES if parent is not None}

    rows = [
        (
            "domain_info_revenue",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in INFO_REVENUE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(INFO_REVENUE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_info_revenue'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_info_revenue'",
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
            [("naics_2022", code, "domain_info_revenue", "primary") for code in naics_codes],
        )

    return count
