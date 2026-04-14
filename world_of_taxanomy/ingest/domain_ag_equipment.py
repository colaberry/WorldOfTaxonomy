"""Agricultural Equipment and Machinery domain taxonomy ingester.

Classifies what physical equipment and machinery is used on the farm -
orthogonal to crop type, livestock, farming method, inputs, business
structure, and market channel. The same tractor can pull a planter on
a corn farm, a mower on a hay operation, or a manure spreader on a
dairy - equipment classification tracks capital asset type, not use case.

Code prefix: dae_
Categories: Tractor and Power Units, Harvest Equipment, Planting and
Seeding Equipment, Irrigation and Water Management, Livestock Equipment,
Precision Agriculture Technology.

Stakeholders: equipment dealers and OEMs (John Deere, CNH, AGCO),
agricultural lenders financing equipment purchases, USDA NASS capital
expenditure surveyors, tax accountants applying Section 179 depreciation,
equipment auction houses.
Source: USDA NASS Farm Production Expenditures, NAEDA equipment dealer
codes, ASABE equipment standards. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_EQUIPMENT_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Tractor and Power Units --
    ("dae_tractor",           "Tractor and Power Units",                              1, None),
    ("dae_tractor_2wd",       "2WD Row-Crop Tractor (under 100 hp)",                 2, "dae_tractor"),
    ("dae_tractor_mfwd",      "MFWD / 4WD Tractor (100-300 hp, standard row-crop)",  2, "dae_tractor"),
    ("dae_tractor_4wd",       "Articulated 4WD Tractor (over 300 hp, large farms)",  2, "dae_tractor"),
    ("dae_tractor_compact",   "Compact Utility Tractor (under 40 hp)",               2, "dae_tractor"),
    ("dae_tractor_track",     "Track or Crawler Tractor (paddy, soft-ground ops)",   2, "dae_tractor"),

    # -- Harvest Equipment --
    ("dae_harvest",           "Harvest Equipment",                                    1, None),
    ("dae_harvest_combine",   "Combine Harvester (grain, corn, soybean)",            2, "dae_harvest"),
    ("dae_harvest_cotton",    "Cotton Picker or Stripper",                            2, "dae_harvest"),
    ("dae_harvest_forage",    "Forage Harvester and Chopper (silage, hay chop)",     2, "dae_harvest"),
    ("dae_harvest_baler",     "Hay Baler (round and square bale)",                   2, "dae_harvest"),
    ("dae_harvest_veg",       "Vegetable and Specialty Crop Harvester",              2, "dae_harvest"),
    ("dae_harvest_grape",     "Grape Harvester and Orchard Platform",                2, "dae_harvest"),

    # -- Planting and Seeding Equipment --
    ("dae_plant",             "Planting and Seeding Equipment",                       1, None),
    ("dae_plant_planter",     "Row-Crop Planter (corn, soybean, cotton, peanut)",    2, "dae_plant"),
    ("dae_plant_drill",       "Grain Drill (wheat, sorghum, small grains)",          2, "dae_plant"),
    ("dae_plant_airseeder",   "Air Seeder (canola, cover crops, large-scale)",       2, "dae_plant"),
    ("dae_plant_transplant",  "Transplanter (tobacco, vegetable, berry)",            2, "dae_plant"),

    # -- Irrigation and Water Management --
    ("dae_irrig",             "Irrigation and Water Management Equipment",            1, None),
    ("dae_irrig_pivot",       "Center Pivot Irrigation System",                      2, "dae_irrig"),
    ("dae_irrig_drip",        "Drip and Micro-Irrigation (high-value crops)",        2, "dae_irrig"),
    ("dae_irrig_flood",       "Flood and Furrow Irrigation (surface water)",         2, "dae_irrig"),
    ("dae_irrig_pump",        "Irrigation Pump and Wellhead Equipment",              2, "dae_irrig"),

    # -- Livestock Equipment --
    ("dae_livestock",         "Livestock Equipment",                                  1, None),
    ("dae_livestock_feed",    "Feed Mixer and Delivery Equipment (TMR wagon)",       2, "dae_livestock"),
    ("dae_livestock_milk",    "Milking Equipment (parlor, robotic milking system)",  2, "dae_livestock"),
    ("dae_livestock_handle",  "Animal Handling and Restraint Equipment",             2, "dae_livestock"),
    ("dae_livestock_waste",   "Manure Management Equipment (spreader, lagoon pump)", 2, "dae_livestock"),
    ("dae_livestock_fence",   "Fencing Systems (electric, high-tensile, corral)",    2, "dae_livestock"),

    # -- Precision Agriculture Technology --
    ("dae_precision",         "Precision Agriculture Technology",                     1, None),
    ("dae_precision_gps",     "GPS Guidance and Auto-Steer Systems",                 2, "dae_precision"),
    ("dae_precision_vra",     "Variable Rate Application Controllers (VRA)",         2, "dae_precision"),
    ("dae_precision_drone",   "Agricultural Drone (scouting, spray, mapping)",       2, "dae_precision"),
    ("dae_precision_sensor",  "In-Field Sensor Networks (soil moisture, weather)",   2, "dae_precision"),
    ("dae_precision_telem",   "Machine Telematics and Fleet Management",             2, "dae_precision"),
]

_DOMAIN_ROW = (
    "domain_ag_equipment",
    "Agricultural Equipment Types",
    "Agricultural equipment and machinery classification - tractor classes, "
    "harvest equipment, planting equipment, irrigation, livestock, and "
    "precision agriculture technology",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific equipment types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_equipment(conn) -> int:
    """Ingest Agricultural Equipment domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_equipment'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_equipment",
        "Agricultural Equipment Types",
        "Agricultural equipment and machinery classification - tractor classes, "
        "harvest equipment, planting equipment, irrigation, livestock, and "
        "precision agriculture technology",
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

    parent_codes = {parent for _, _, _, parent in AG_EQUIPMENT_NODES if parent is not None}

    rows = [
        (
            "domain_ag_equipment",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_EQUIPMENT_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_EQUIPMENT_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_equipment'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_equipment'",
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
            [("naics_2022", code, "domain_ag_equipment", "primary") for code in naics_codes],
        )

    return count
