"""Food Service and Hospitality Ownership and Franchise Model Types domain taxonomy ingester.

Food service and hospitality ownership structure and franchise model classification.

Code prefix: dfsown_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
FOOD_OWNERSHIP_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Franchise and Licensed Brand Models --
    ("dfsown_franchise", "Franchise and Licensed Brand Models", 1, None),
    ("dfsown_franchise_branded", "Branded Franchise (QSR - McDonald's, Subway, Hilton)", 2, 'dfsown_franchise'),
    ("dfsown_franchise_soft", "Soft Brand and Curio Collection (independent affiliation)", 2, 'dfsown_franchise'),
    ("dfsown_franchise_area", "Area Developer and Multi-Unit Franchise Agreement", 2, 'dfsown_franchise'),
    # -- Management Contract and Third-Party Operations --
    ("dfsown_managed", "Management Contract and Third-Party Operations", 1, None),
    ("dfsown_managed_hotel", "Hotel Management Company (Aimbridge, Sage, White Lodging)", 2, 'dfsown_managed'),
    ("dfsown_managed_food", "Contract Food Service Management (Aramark, Sodexo, Compass)", 2, 'dfsown_managed'),
    # -- Independent and Owner-Operated --
    ("dfsown_independent", "Independent and Owner-Operated", 1, None),
    ("dfsown_independent_single", "Single-Location Independent Restaurant or Hotel", 2, 'dfsown_independent'),
    ("dfsown_independent_group", "Independent Multi-Concept Restaurant Group", 2, 'dfsown_independent'),
    # -- Corporate and Institutional Food Service --
    ("dfsown_corporate", "Corporate and Institutional Food Service", 1, None),
    ("dfsown_corporate_campus", "Corporate Campus and Employee Dining", 2, 'dfsown_corporate'),
    ("dfsown_corporate_health", "Healthcare Food Service (hospital, long-term care)", 2, 'dfsown_corporate'),
    # -- Institutional and Public Sector Food Service --
    ("dfsown_institutional", "Institutional and Public Sector Food Service", 1, None),
    ("dfsown_institutional_school", "K-12 School Nutrition and Cafeteria Service", 2, 'dfsown_institutional'),
    ("dfsown_institutional_govt", "Government and Military Food Service (AAFES, DFAC)", 2, 'dfsown_institutional'),
]

_DOMAIN_ROW = (
    "domain_food_ownership",
    "Food Service and Hospitality Ownership and Franchise Model Types",
    "Food service and hospitality ownership structure and franchise model classification",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['72']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_food_ownership(conn) -> int:
    """Ingest Food Service and Hospitality Ownership and Franchise Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_food_ownership",
        "Food Service and Hospitality Ownership and Franchise Model Types",
        "Food service and hospitality ownership structure and franchise model classification",
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

    parent_codes = {parent for _, _, _, parent in FOOD_OWNERSHIP_NODES if parent is not None}

    rows = [
        (
            "domain_food_ownership",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in FOOD_OWNERSHIP_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(FOOD_OWNERSHIP_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_food_ownership'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_food_ownership'",
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
            [("naics_2022", code, "domain_food_ownership", "primary") for code in naics_codes],
        )

    return count
