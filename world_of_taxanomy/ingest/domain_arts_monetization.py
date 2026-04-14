"""Arts and Entertainment Monetization and Distribution Model Types domain taxonomy ingester.

Arts and entertainment monetization and distribution model classification - ticket-based, subscription, advertising, patronage, licensing.

Code prefix: dacmon_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
ARTS_MONETIZATION_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Ticket and Admission-Based Revenue --
    ("dacmon_ticket", "Ticket and Admission-Based Revenue", 1, None),
    ("dacmon_ticket_live", "Live Event Ticketing (concert, theater, sports)", 2, 'dacmon_ticket'),
    ("dacmon_ticket_dynamic", "Dynamic and Secondary Market Ticketing (StubHub, Tixr)", 2, 'dacmon_ticket'),
    ("dacmon_ticket_vip", "VIP and Premium Experience Packages", 2, 'dacmon_ticket'),
    # -- Subscription and Membership Revenue --
    ("dacmon_subscription", "Subscription and Membership Revenue", 1, None),
    ("dacmon_subscription_svod", "SVOD Subscription (Netflix, HBO Max, Disney+)", 2, 'dacmon_subscription'),
    ("dacmon_subscription_music", "Music Streaming Subscription (Spotify, Apple Music)", 2, 'dacmon_subscription'),
    ("dacmon_subscription_fan", "Fan Club and Creator Subscription (Patreon, Substack)", 2, 'dacmon_subscription'),
    # -- Advertising and Sponsored Content --
    ("dacmon_advertising", "Advertising and Sponsored Content", 1, None),
    ("dacmon_advertising_avod", "AVOD and FAST Channels (Tubi, Pluto TV, Peacock Free)", 2, 'dacmon_advertising'),
    ("dacmon_advertising_brand", "Brand Sponsorship and Naming Rights", 2, 'dacmon_advertising'),
    # -- Patronage, Grants, and Public Funding --
    ("dacmon_patronage", "Patronage, Grants, and Public Funding", 1, None),
    ("dacmon_patronage_nea", "NEA and State Arts Council Grants", 2, 'dacmon_patronage'),
    ("dacmon_patronage_foundation", "Private Foundation and Endowment Support", 2, 'dacmon_patronage'),
    # -- IP Licensing and Sync Revenue --
    ("dacmon_licensing", "IP Licensing and Sync Revenue", 1, None),
    ("dacmon_licensing_sync", "Sync Licensing (music in film, TV, advertising)", 2, 'dacmon_licensing'),
    ("dacmon_licensing_merch", "Merchandise and Branded Product Licensing", 2, 'dacmon_licensing'),
    ("dacmon_licensing_theme", "Theme Park and Character Licensing", 2, 'dacmon_licensing'),
]

_DOMAIN_ROW = (
    "domain_arts_monetization",
    "Arts and Entertainment Monetization and Distribution Model Types",
    "Arts and entertainment monetization and distribution model classification - ticket-based, subscription, advertising, patronage, licensing",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['71']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_arts_monetization(conn) -> int:
    """Ingest Arts and Entertainment Monetization and Distribution Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_arts_monetization",
        "Arts and Entertainment Monetization and Distribution Model Types",
        "Arts and entertainment monetization and distribution model classification - ticket-based, subscription, advertising, patronage, licensing",
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

    parent_codes = {parent for _, _, _, parent in ARTS_MONETIZATION_NODES if parent is not None}

    rows = [
        (
            "domain_arts_monetization",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in ARTS_MONETIZATION_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(ARTS_MONETIZATION_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_arts_monetization'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_arts_monetization'",
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
            [("naics_2022", code, "domain_arts_monetization", "primary") for code in naics_codes],
        )

    return count
