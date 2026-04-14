"""Truck Geographic Lane Classification domain taxonomy ingester.

Classifies truck freight lanes by geographic characteristics - orthogonal to
freight mode (LTL/FTL), vehicle class, cargo type, carrier ops, pricing,
regulatory domains, and technology level. The same FTL dry van carrier with
a contract rate and ELD compliance operates differently on a 50-mile local
lane vs. a 2,000-mile OTR lane vs. a US-Mexico cross-border lane.

Code prefix: dtl_
Categories: Haul Distance, Geographic Corridor, Cross-Border/International,
Last Mile Classification, Lane Market Density.

Stakeholders: network planners, lane rate analysts, load matchers, capacity
brokers, real estate site selectors (warehouse placement), fuel planners.
Source: DAT lane analytics, FMCSA Freight Analysis Framework (FAF),
ATRI corridor studies, CBP cross-border data. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
LANE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Haul Distance Classification --
    ("dtl_dist",              "Haul Distance Classification",                      1, None),
    ("dtl_dist_local",        "Local (under 50 miles / same metro area)",          2, "dtl_dist"),
    ("dtl_dist_short",        "Short Haul (50-250 miles)",                         2, "dtl_dist"),
    ("dtl_dist_regional",     "Regional (250-500 miles, day cab territory)",        2, "dtl_dist"),
    ("dtl_dist_longhaul",     "Long Haul (500-1,500 miles)",                        2, "dtl_dist"),
    ("dtl_dist_otr",          "Over-the-Road OTR (1,500+ miles, sleeper cab)",     2, "dtl_dist"),

    # -- Geographic Corridor --
    ("dtl_geo",               "Geographic Corridor",                               1, None),
    ("dtl_geo_ne",            "Northeast Corridor (BOS-NYC-PHL-DC-BAL)",           2, "dtl_geo"),
    ("dtl_geo_se",            "Southeast (ATL-MIA-CHA-RIC hub region)",            2, "dtl_geo"),
    ("dtl_geo_mw",            "Midwest (Chicago hub, Great Lakes, Ohio Valley)",   2, "dtl_geo"),
    ("dtl_geo_sw",            "Southwest (TX, AZ, NM, OK)",                        2, "dtl_geo"),
    ("dtl_geo_nw",            "Northwest / Pacific Northwest (PNW, ID, MT)",       2, "dtl_geo"),
    ("dtl_geo_ca",            "California / West Coast (CARB regulatory zone)",    2, "dtl_geo"),
    ("dtl_geo_central",       "Central Plains (Grain Belt: KS, NE, IA, MN)",       2, "dtl_geo"),
    ("dtl_geo_appalachian",   "Appalachian / Mid-South (WV, KY, TN, AR)",          2, "dtl_geo"),
    ("dtl_geo_intercoastal",  "Intercoastal Transcontinental (East-West I-80/I-90)", 2, "dtl_geo"),

    # -- Cross-Border and International --
    ("dtl_border",            "Cross-Border and International",                    1, None),
    ("dtl_border_us_ca",      "US-Canada Cross-Border (USMCA, CBSA clearance)",   2, "dtl_border"),
    ("dtl_border_us_mx",      "US-Mexico Cross-Border (USMCA, Drayage at POE)",   2, "dtl_border"),
    ("dtl_border_transship",  "International Transshipment / NVOCC Drayage",       2, "dtl_border"),
    ("dtl_border_ftz",        "Free Trade Zone / Foreign Trade Zone (FTZ) Lane",   2, "dtl_border"),

    # -- Last Mile / Final Delivery --
    ("dtl_lastmile",          "Last Mile / Final Delivery Classification",         1, None),
    ("dtl_lastmile_urban",    "Urban Last Mile (dense city center, stop-heavy)",   2, "dtl_lastmile"),
    ("dtl_lastmile_suburban", "Suburban Last Mile (residential neighborhoods)",    2, "dtl_lastmile"),
    ("dtl_lastmile_rural",    "Rural Last Mile (low-density, extended reach)",     2, "dtl_lastmile"),
    ("dtl_lastmile_resi",     "Residential Delivery (home / apartment delivery)",  2, "dtl_lastmile"),
    ("dtl_lastmile_commercial","Commercial Delivery (dock, forklift, scheduled)",  2, "dtl_lastmile"),
    ("dtl_lastmile_ondemand", "On-Demand / Same-Day Delivery (e-commerce, hot shot)", 2, "dtl_lastmile"),

    # -- Lane Market Density --
    ("dtl_density",           "Lane Market Density",                               1, None),
    ("dtl_density_high",      "High-Density Lane (many carriers, competitive spot market)", 2, "dtl_density"),
    ("dtl_density_medium",    "Medium-Density Lane (moderate carrier availability)", 2, "dtl_density"),
    ("dtl_density_low",       "Low-Density / Capacity-Constrained Lane",           2, "dtl_density"),
    ("dtl_density_backhaul",  "Backhaul Lane (return trip, soft rates, low demand)", 2, "dtl_density"),
    ("dtl_density_headhaul",  "Headhaul Lane (outbound, tight capacity, strong rates)", 2, "dtl_density"),
]

_DOMAIN_ROW = (
    "domain_truck_lane",
    "Truck Geographic Lane Classification",
    "Classifies truck freight lanes by geographic characteristics: haul distance, "
    "corridor type, cross-border, last mile, and lane market density",
    "WorldOfTaxanomy",
    None,
)

# NAICS 484: Truck Transportation (all sub-sectors)
_NAICS_PREFIXES = ["484"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories (dtl_xxx), 2 for specific types (dtl_xxx_yyy)."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_truck_lane(conn) -> int:
    """Ingest Truck Geographic Lane Classification domain taxonomy.

    Registers in classification_system and domain_taxonomy, stores nodes
    in classification_node (system_id='domain_truck_lane'), and links
    all NAICS 484xxx nodes via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_truck_lane",
        "Truck Geographic Lane Classification",
        "Classifies truck freight lanes by geographic characteristics: haul distance, "
        "corridor type, cross-border, last mile, and lane market density",
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

    parent_codes = {parent for _, _, _, parent in LANE_NODES if parent is not None}

    rows = [
        (
            "domain_truck_lane",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in LANE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(LANE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_truck_lane'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_truck_lane'",
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
            [("naics_2022", code, "domain_truck_lane", "primary") for code in naics_codes],
        )

    return count
