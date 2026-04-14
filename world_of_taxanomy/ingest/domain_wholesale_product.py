"""Wholesale Trade Product Category Types domain taxonomy ingester.

Wholesale trade product category classification - food/bev, pharma, industrial, building materials, technology, farm supplies.

Code prefix: dwcprod_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
WHOLESALE_PRODUCT_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Food and Beverage Wholesale --
    ("dwcprod_food", "Food and Beverage Wholesale", 1, None),
    ("dwcprod_food_fresh", "Fresh Produce and Perishables Distribution", 2, 'dwcprod_food'),
    ("dwcprod_food_dry", "Dry Grocery and Packaged Foods Distribution", 2, 'dwcprod_food'),
    ("dwcprod_food_bev", "Beverage Distribution (beer, wine, spirits, soft drinks)", 2, 'dwcprod_food'),
    # -- Pharmaceutical and Health Products Wholesale --
    ("dwcprod_pharma", "Pharmaceutical and Health Products Wholesale", 1, None),
    ("dwcprod_pharma_rx", "Prescription Drug Distribution (AmerisourceBergen, McKesson)", 2, 'dwcprod_pharma'),
    ("dwcprod_pharma_otc", "OTC and Health Beauty Aid Distribution", 2, 'dwcprod_pharma'),
    # -- Industrial and Commercial Supplies --
    ("dwcprod_industrial", "Industrial and Commercial Supplies", 1, None),
    ("dwcprod_industrial_mro", "MRO Supplies (Grainger, Fastenal, W.W. Grainger)", 2, 'dwcprod_industrial'),
    ("dwcprod_industrial_safety", "Safety Products and Workplace Equipment", 2, 'dwcprod_industrial'),
    # -- Building Materials and Construction Supplies --
    ("dwcprod_building", "Building Materials and Construction Supplies", 1, None),
    ("dwcprod_building_lumber", "Lumber and Wood Products Distribution", 2, 'dwcprod_building'),
    ("dwcprod_building_hvac", "HVAC, Plumbing, and Electrical Wholesale", 2, 'dwcprod_building'),
    # -- Technology and Electronics Distribution --
    ("dwcprod_tech", "Technology and Electronics Distribution", 1, None),
    ("dwcprod_tech_it", "IT Hardware and Components Distribution (Ingram, TD SYNNEX)", 2, 'dwcprod_tech'),
    ("dwcprod_tech_av", "Audio/Visual and Security Equipment Distribution", 2, 'dwcprod_tech'),
    # -- Farm Supply and Agricultural Inputs --
    ("dwcprod_farm", "Farm Supply and Agricultural Inputs", 1, None),
    ("dwcprod_farm_seed", "Seed, Fertilizer, and Agrochemical Distribution", 2, 'dwcprod_farm'),
    ("dwcprod_farm_equip", "Farm Equipment and Parts Distribution", 2, 'dwcprod_farm'),
]

_DOMAIN_ROW = (
    "domain_wholesale_product",
    "Wholesale Trade Product Category Types",
    "Wholesale trade product category classification - food/bev, pharma, industrial, building materials, technology, farm supplies",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['42']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_wholesale_product(conn) -> int:
    """Ingest Wholesale Trade Product Category Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_wholesale_product",
        "Wholesale Trade Product Category Types",
        "Wholesale trade product category classification - food/bev, pharma, industrial, building materials, technology, farm supplies",
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

    parent_codes = {parent for _, _, _, parent in WHOLESALE_PRODUCT_NODES if parent is not None}

    rows = [
        (
            "domain_wholesale_product",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in WHOLESALE_PRODUCT_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(WHOLESALE_PRODUCT_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_wholesale_product'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_wholesale_product'",
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
            [("naics_2022", code, "domain_wholesale_product", "primary") for code in naics_codes],
        )

    return count
