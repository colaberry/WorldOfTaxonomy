"""Truck Pricing / Rate Structure domain taxonomy ingester.

Classifies how truck freight is priced - orthogonal to freight mode, vehicle
class, cargo type, and carrier operations. A single shipment has one rate
structure (spot vs. contract), one fuel surcharge type, and may incur several
accessorial charges, all billed on a specific rating basis.

Code prefix: dtp_
Categories: Rate Structure, Fuel Surcharge, Accessorial Charges, Rating Basis.

Stakeholders: rate desks, TMS rating engines, shippers, freight auditors,
brokers, procurement teams running RFPs.
Source: NMFC tariff structure, DAT rate analytics, UPS/FedEx accessorial
schedules, FMCSA fuel surcharge index. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
PRICING_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Rate Structure Type --
    ("dtp_rate",            "Rate Structure Type",                               1, None),
    ("dtp_rate_spot",       "Spot Rate (market rate, single load)",              2, "dtp_rate"),
    ("dtp_rate_contract",   "Contract Rate (annual / multi-year negotiated)",    2, "dtp_rate"),
    ("dtp_rate_tariff",     "Published Tariff Rate (NMFC / carrier tariff)",     2, "dtp_rate"),
    ("dtp_rate_quote",      "Quoted Rate (shipper-requested price quote)",        2, "dtp_rate"),
    ("dtp_rate_bid",        "Bid / RFP Rate (procurement tender award)",         2, "dtp_rate"),
    ("dtp_rate_index",      "Index-Linked Rate (DAT / Truckstop spot index)",    2, "dtp_rate"),

    # -- Fuel Surcharge Types --
    ("dtp_fsc",             "Fuel Surcharge Type",                               1, None),
    ("dtp_fsc_doe",         "DOE Index-Based Fuel Surcharge (weekly DOE table)", 2, "dtp_fsc"),
    ("dtp_fsc_flat",        "Flat Per-Mile Fuel Surcharge",                      2, "dtp_fsc"),
    ("dtp_fsc_pct",         "Percentage Fuel Surcharge (% of base line-haul)",  2, "dtp_fsc"),
    ("dtp_fsc_allin",       "All-In Rate (fuel included, no separate FSC)",     2, "dtp_fsc"),
    ("dtp_fsc_dynamic",     "Dynamic / Real-Time Fuel Pricing",                  2, "dtp_fsc"),

    # -- Accessorial Charges --
    ("dtp_acc",             "Accessorial Charges",                               1, None),
    ("dtp_acc_lift",        "Liftgate Pickup or Delivery",                       2, "dtp_acc"),
    ("dtp_acc_det",         "Detention / Driver Wait Time (beyond free time)",   2, "dtp_acc"),
    ("dtp_acc_res",         "Residential Delivery Surcharge",                    2, "dtp_acc"),
    ("dtp_acc_inside",      "Inside Delivery (beyond threshold)",                2, "dtp_acc"),
    ("dtp_acc_redeliver",   "Redelivery Fee (first attempt failed)",             2, "dtp_acc"),
    ("dtp_acc_overlength",  "Overlength / Oversize Surcharge",                   2, "dtp_acc"),
    ("dtp_acc_overweight",  "Overweight Permit / Superload Fee",                 2, "dtp_acc"),
    ("dtp_acc_hazmat",      "Hazmat Handling Fee (DOT regulated)",               2, "dtp_acc"),
    ("dtp_acc_temp",        "Temperature Protection / Freeze Protection Fee",    2, "dtp_acc"),
    ("dtp_acc_sort",        "Sort and Segregate / Piece-Count Service",          2, "dtp_acc"),
    ("dtp_acc_appt",        "Appointment Scheduling Fee",                        2, "dtp_acc"),
    ("dtp_acc_storage",     "Storage / Demurrage (facility hold charge)",        2, "dtp_acc"),

    # -- Rating Basis / Unit of Measure --
    ("dtp_unit",            "Rating Basis / Unit of Measure",                    1, None),
    ("dtp_unit_mile",       "Per-Mile (line-haul rate per loaded mile)",         2, "dtp_unit"),
    ("dtp_unit_cwt",        "Per-Hundredweight / CWT (LTL standard)",            2, "dtp_unit"),
    ("dtp_unit_pallet",     "Per-Pallet Pricing",                                2, "dtp_unit"),
    ("dtp_unit_cube",       "Per-Cubic-Foot / Density-Based Pricing",            2, "dtp_unit"),
    ("dtp_unit_ship",       "Per-Shipment Flat Rate",                            2, "dtp_unit"),
    ("dtp_unit_lane",       "Lane-Based All-In Rate (origin-destination pair)",  2, "dtp_unit"),
    ("dtp_unit_load",       "Per-Load (FTL flat load rate)",                     2, "dtp_unit"),
]

_DOMAIN_ROW = (
    "domain_truck_pricing",
    "Truck Pricing and Rate Structure Types",
    "Classifies how truck freight is priced: rate structures, fuel surcharges, "
    "accessorial charges, and rating basis units",
    "WorldOfTaxanomy",
    None,
)

# NAICS 484: Truck Transportation (all sub-sectors)
_NAICS_PREFIXES = ["484"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories (dtp_xxx), 2 for specific types (dtp_xxx_yyy)."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_truck_pricing(conn) -> int:
    """Ingest Truck Pricing / Rate Structure domain taxonomy.

    Registers in classification_system and domain_taxonomy, stores nodes
    in classification_node (system_id='domain_truck_pricing'), and links
    all NAICS 484xxx nodes via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_truck_pricing",
        "Truck Pricing and Rate Structure",
        "Classifies how truck freight is priced: rate structures, fuel surcharges, "
        "accessorial charges, and rating basis units",
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

    parent_codes = {parent for _, _, _, parent in PRICING_NODES if parent is not None}

    rows = [
        (
            "domain_truck_pricing",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in PRICING_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(PRICING_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_truck_pricing'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_truck_pricing'",
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
            [("naics_2022", code, "domain_truck_pricing", "primary") for code in naics_codes],
        )

    return count
