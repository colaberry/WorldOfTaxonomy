"""Other Services Pricing and Business Model Types domain taxonomy ingester.

Other services pricing and business model classification - per-service, subscription, membership, bundled, hourly.

Code prefix: dosprice_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
OTHER_PRICING_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Per-Service and Transaction Pricing --
    ("dosprice_perservice", "Per-Service and Transaction Pricing", 1, None),
    ("dosprice_perservice_flat", "Flat Rate Per Service (one price per visit or job)", 2, 'dosprice_perservice'),
    ("dosprice_perservice_tiered", "Tiered Pricing (small/medium/large job size)", 2, 'dosprice_perservice'),
    # -- Subscription and Recurring Service Models --
    ("dosprice_subscription", "Subscription and Recurring Service Models", 1, None),
    ("dosprice_subscription_monthly", "Monthly Recurring Subscription (lawn, pest, cleaning)", 2, 'dosprice_subscription'),
    ("dosprice_subscription_annual", "Annual Service Agreement (HVAC, appliance maintenance)", 2, 'dosprice_subscription'),
    # -- Bundled Service Packages --
    ("dosprice_bundled", "Bundled Service Packages", 1, None),
    ("dosprice_bundled_package", "Service Bundle (multiple services at package price)", 2, 'dosprice_bundled'),
    ("dosprice_bundled_insurance", "Insurance and Warranty-Based Service Contract", 2, 'dosprice_bundled'),
    # -- Time-Based and Hourly Pricing --
    ("dosprice_hourly", "Time-Based and Hourly Pricing", 1, None),
    ("dosprice_hourly_standard", "Standard Hourly Rate (labor + materials)", 2, 'dosprice_hourly'),
    ("dosprice_hourly_emergency", "Emergency and After-Hours Premium Rate", 2, 'dosprice_hourly'),
    # -- Club and Membership Pricing --
    ("dosprice_membership", "Club and Membership Pricing", 1, None),
    ("dosprice_membership_gym", "Gym and Fitness Club Membership", 2, 'dosprice_membership'),
    ("dosprice_membership_trade", "Trade Association Member Pricing", 2, 'dosprice_membership'),
]

_DOMAIN_ROW = (
    "domain_other_pricing",
    "Other Services Pricing and Business Model Types",
    "Other services pricing and business model classification - per-service, subscription, membership, bundled, hourly",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['81']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_other_pricing(conn) -> int:
    """Ingest Other Services Pricing and Business Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_other_pricing",
        "Other Services Pricing and Business Model Types",
        "Other services pricing and business model classification - per-service, subscription, membership, bundled, hourly",
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

    parent_codes = {parent for _, _, _, parent in OTHER_PRICING_NODES if parent is not None}

    rows = [
        (
            "domain_other_pricing",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in OTHER_PRICING_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(OTHER_PRICING_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_other_pricing'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_other_pricing'",
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
            [("naics_2022", code, "domain_other_pricing", "primary") for code in naics_codes],
        )

    return count
