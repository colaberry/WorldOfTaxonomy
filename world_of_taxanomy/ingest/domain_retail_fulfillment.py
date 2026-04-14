"""Retail Fulfillment and Last-Mile Delivery Model Types domain taxonomy ingester.

Retail fulfillment and last-mile delivery model classification - ship-from-store, BOPIS, direct ship, same-day, returns.

Code prefix: drcfulfl_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
RETAIL_FULFILLMENT_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Store-Based Fulfillment Models --
    ("drcfulfl_store", "Store-Based Fulfillment Models", 1, None),
    ("drcfulfl_store_ship", "Ship-from-Store (store inventory fulfills online orders)", 2, 'drcfulfl_store'),
    ("drcfulfl_store_curbside", "Curbside Pickup", 2, 'drcfulfl_store'),
    # -- Buy Online, Pick Up In Store (BOPIS) --
    ("drcfulfl_bopis", "Buy Online, Pick Up In Store (BOPIS) and Click-and-Collect", 1, None),
    ("drcfulfl_bopis_instore", "In-Store Pickup (designated pickup counter or locker)", 2, 'drcfulfl_bopis'),
    ("drcfulfl_bopis_locker", "Smart Locker and Automated Pickup System", 2, 'drcfulfl_bopis'),
    # -- Direct Ship and Warehouse Fulfillment --
    ("drcfulfl_direct", "Direct Ship and Warehouse Fulfillment", 1, None),
    ("drcfulfl_direct_3pl", "3PL Fulfillment Center (outsourced warehouse and ship)", 2, 'drcfulfl_direct'),
    ("drcfulfl_direct_amazon", "Amazon FBA / Marketplace Fulfillment", 2, 'drcfulfl_direct'),
    ("drcfulfl_direct_dropship", "Vendor Drop-Ship (supplier ships direct to customer)", 2, 'drcfulfl_direct'),
    # -- Same-Day and Rapid Delivery --
    ("drcfulfl_sameday", "Same-Day and Rapid Delivery", 1, None),
    ("drcfulfl_sameday_grocery", "Grocery Same-Day Delivery (Instacart, Shipt)", 2, 'drcfulfl_sameday'),
    ("drcfulfl_sameday_q", "Quick Commerce (15-30 min dark store delivery)", 2, 'drcfulfl_sameday'),
    ("drcfulfl_sameday_ld", "Same-Day Last Mile (DoorDash Drive, Roadie)", 2, 'drcfulfl_sameday'),
    # -- Returns Management and Reverse Logistics --
    ("drcfulfl_returns", "Returns Management and Reverse Logistics", 1, None),
    ("drcfulfl_returns_instore", "In-Store Returns Processing", 2, 'drcfulfl_returns'),
    ("drcfulfl_returns_mail", "Prepaid Return Label Mail-Back", 2, 'drcfulfl_returns'),
    ("drcfulfl_returns_happy", "Happy Returns / Returns Drop-off Hub", 2, 'drcfulfl_returns'),
]

_DOMAIN_ROW = (
    "domain_retail_fulfillment",
    "Retail Fulfillment and Last-Mile Delivery Model Types",
    "Retail fulfillment and last-mile delivery model classification - ship-from-store, BOPIS, direct ship, same-day, returns",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['44', '45']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_retail_fulfillment(conn) -> int:
    """Ingest Retail Fulfillment and Last-Mile Delivery Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_retail_fulfillment",
        "Retail Fulfillment and Last-Mile Delivery Model Types",
        "Retail fulfillment and last-mile delivery model classification - ship-from-store, BOPIS, direct ship, same-day, returns",
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

    parent_codes = {parent for _, _, _, parent in RETAIL_FULFILLMENT_NODES if parent is not None}

    rows = [
        (
            "domain_retail_fulfillment",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in RETAIL_FULFILLMENT_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(RETAIL_FULFILLMENT_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_retail_fulfillment'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_retail_fulfillment'",
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
            [("naics_2022", code, "domain_retail_fulfillment", "primary") for code in naics_codes],
        )

    return count
