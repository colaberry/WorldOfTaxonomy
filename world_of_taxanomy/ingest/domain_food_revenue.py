"""Food Service and Hospitality Revenue Management Types domain taxonomy ingester.

Food service and hospitality revenue management and pricing classification - RevPAR, covers, ADR, catering, ancillary.

Code prefix: dfsrev_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
FOOD_REVENUE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Lodging Revenue Management --
    ("dfsrev_room", "Lodging Revenue Management", 1, None),
    ("dfsrev_room_revpar", "RevPAR-Based Yield Management (ADR x Occupancy)", 2, 'dfsrev_room'),
    ("dfsrev_room_length", "Length-of-Stay Pricing (LOS restrictions, packages)", 2, 'dfsrev_room'),
    ("dfsrev_room_ota", "OTA and GDS Channel Pricing (Booking, Expedia, GDS)", 2, 'dfsrev_room'),
    # -- Food and Beverage Revenue Management --
    ("dfsrev_fb", "Food and Beverage Revenue Management", 1, None),
    ("dfsrev_fb_covers", "Cover-Based Pricing (RevPASH - revenue per available seat hour)", 2, 'dfsrev_fb'),
    ("dfsrev_fb_prix", "Prix Fixe and Tasting Menu Pricing", 2, 'dfsrev_fb'),
    ("dfsrev_fb_dynamic", "Dynamic Menu Pricing (surge pricing, daypart variation)", 2, 'dfsrev_fb'),
    # -- Event and Group Revenue Management --
    ("dfsrev_event", "Event and Group Revenue Management", 1, None),
    ("dfsrev_event_catering", "Catering and Banquet Function Revenue", 2, 'dfsrev_event'),
    ("dfsrev_event_meeting", "Meeting and Convention Space Revenue (SMERF, corporate)", 2, 'dfsrev_event'),
    # -- Ancillary and Total Revenue Management --
    ("dfsrev_ancillary", "Ancillary and Total Revenue Management", 1, None),
    ("dfsrev_ancillary_spa", "Spa, Golf, and Recreational Amenity Revenue", 2, 'dfsrev_ancillary'),
    ("dfsrev_ancillary_parking", "Parking and Transportation Revenue", 2, 'dfsrev_ancillary'),
    ("dfsrev_ancillary_retail", "Retail and Gift Shop Revenue (branded merchandise)", 2, 'dfsrev_ancillary'),
]

_DOMAIN_ROW = (
    "domain_food_revenue",
    "Food Service and Hospitality Revenue Management Types",
    "Food service and hospitality revenue management and pricing classification - RevPAR, covers, ADR, catering, ancillary",
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


async def ingest_domain_food_revenue(conn) -> int:
    """Ingest Food Service and Hospitality Revenue Management Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_food_revenue",
        "Food Service and Hospitality Revenue Management Types",
        "Food service and hospitality revenue management and pricing classification - RevPAR, covers, ADR, catering, ancillary",
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

    parent_codes = {parent for _, _, _, parent in FOOD_REVENUE_NODES if parent is not None}

    rows = [
        (
            "domain_food_revenue",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in FOOD_REVENUE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(FOOD_REVENUE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_food_revenue'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_food_revenue'",
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
            [("naics_2022", code, "domain_food_revenue", "primary") for code in naics_codes],
        )

    return count
