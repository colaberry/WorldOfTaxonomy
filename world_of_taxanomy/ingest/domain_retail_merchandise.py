"""Retail Merchandise and Product Category Types domain taxonomy ingester.

Retail merchandise and product category classification - grocery, apparel, electronics, home goods, auto parts, health and beauty.

Code prefix: drcmerch_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
RETAIL_MERCH_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Grocery and Food Retail --
    ("drcmerch_grocery", "Grocery and Food Retail", 1, None),
    ("drcmerch_grocery_fresh", "Fresh Produce and Perishables", 2, 'drcmerch_grocery'),
    ("drcmerch_grocery_cpg", "Packaged Consumer Goods (CPG - center store)", 2, 'drcmerch_grocery'),
    ("drcmerch_grocery_nat", "Natural, Organic, and Specialty Food", 2, 'drcmerch_grocery'),
    # -- Apparel, Footwear, and Accessories --
    ("drcmerch_apparel", "Apparel, Footwear, and Accessories", 1, None),
    ("drcmerch_apparel_fast", "Fast Fashion and Mass Market Apparel", 2, 'drcmerch_apparel'),
    ("drcmerch_apparel_luxury", "Luxury and Premium Apparel and Accessories", 2, 'drcmerch_apparel'),
    ("drcmerch_apparel_sport", "Athletic and Activewear", 2, 'drcmerch_apparel'),
    # -- Consumer Electronics and Technology --
    ("drcmerch_electronics", "Consumer Electronics and Technology", 1, None),
    ("drcmerch_electronics_phone", "Smartphones and Mobile Devices", 2, 'drcmerch_electronics'),
    ("drcmerch_electronics_ce", "Consumer Electronics (TV, audio, PC, gaming)", 2, 'drcmerch_electronics'),
    # -- Home Goods, Furniture, and Improvement --
    ("drcmerch_home", "Home Goods, Furniture, and Improvement", 1, None),
    ("drcmerch_home_furn", "Furniture and Home Furnishings", 2, 'drcmerch_home'),
    ("drcmerch_home_improve", "Home Improvement and Hardware", 2, 'drcmerch_home'),
    # -- Health, Beauty, and Personal Care --
    ("drcmerch_health", "Health, Beauty, and Personal Care", 1, None),
    ("drcmerch_health_otc", "OTC Drugs, Vitamins, and Supplements", 2, 'drcmerch_health'),
    ("drcmerch_health_beauty", "Beauty, Cosmetics, and Personal Care Products", 2, 'drcmerch_health'),
    # -- Automotive Parts and Accessories --
    ("drcmerch_auto", "Automotive Parts and Accessories", 1, None),
    ("drcmerch_auto_parts", "Replacement Parts and Accessories (AutoZone, O'Reilly)", 2, 'drcmerch_auto'),
    ("drcmerch_auto_new", "New and Used Vehicle Retail (dealer franchise)", 2, 'drcmerch_auto'),
]

_DOMAIN_ROW = (
    "domain_retail_merchandise",
    "Retail Merchandise and Product Category Types",
    "Retail merchandise and product category classification - grocery, apparel, electronics, home goods, auto parts, health and beauty",
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


async def ingest_domain_retail_merchandise(conn) -> int:
    """Ingest Retail Merchandise and Product Category Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_retail_merchandise",
        "Retail Merchandise and Product Category Types",
        "Retail merchandise and product category classification - grocery, apparel, electronics, home goods, auto parts, health and beauty",
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

    parent_codes = {parent for _, _, _, parent in RETAIL_MERCH_NODES if parent is not None}

    rows = [
        (
            "domain_retail_merchandise",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in RETAIL_MERCH_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(RETAIL_MERCH_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_retail_merchandise'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_retail_merchandise'",
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
            [("naics_2022", code, "domain_retail_merchandise", "primary") for code in naics_codes],
        )

    return count
