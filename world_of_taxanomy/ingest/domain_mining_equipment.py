"""Mining Equipment and Machinery domain taxonomy ingester.

Classifies what physical equipment and machinery is deployed at a mine -
orthogonal to mineral type, extraction method, and reserve classification.
The same rope shovel loads copper ore in an open-pit mine and coal in a
surface mine. A rotary drill operates in both gold and iron ore environments.

Code prefix: dmq_
Categories: Drilling and Blasting Equipment, Loading and Hauling Equipment,
Underground Equipment, Processing and Beneficiation Equipment, Safety and
Support Equipment.

Stakeholders: mining equipment OEMs (Caterpillar, Komatsu, Sandvik, Epiroc),
mine planners doing fleet optimization, equipment finance and insurance,
MSHA equipment inspection, mine safety officers.
Source: SME Mining Engineering Handbook, Caterpillar mining product
classifications, Sandvik product categories. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MINING_EQUIPMENT_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Drilling and Blasting Equipment --
    ("dmq_drill",             "Drilling and Blasting Equipment",               1, None),
    ("dmq_drill_rotary",      "Rotary Blast Hole Drill (surface, large diameter)", 2, "dmq_drill"),
    ("dmq_drill_dth",         "Down-the-Hole (DTH) Drill",                    2, "dmq_drill"),
    ("dmq_drill_top",         "Top Hammer Drill Rig",                         2, "dmq_drill"),
    ("dmq_drill_raise",       "Raise Bore and Shaft Sinking Equipment",       2, "dmq_drill"),
    ("dmq_drill_blast",       "Blasting Accessories and Explosives Delivery", 2, "dmq_drill"),

    # -- Loading and Hauling Equipment --
    ("dmq_load",              "Loading and Hauling Equipment",                 1, None),
    ("dmq_load_haul",         "Ultra-Class Haul Truck (150-400 ton payload)",  2, "dmq_load"),
    ("dmq_load_shovel",       "Electric Rope Shovel (surface, large capacity)", 2, "dmq_load"),
    ("dmq_load_excavator",    "Hydraulic Mining Excavator",                   2, "dmq_load"),
    ("dmq_load_loader",       "Wheel Loader (surface ore and waste loading)",  2, "dmq_load"),
    ("dmq_load_dozer",        "Mining Bulldozer (push, rip, reclaim)",         2, "dmq_load"),
    ("dmq_load_conveyor",     "Overland and In-Pit Conveyor System",          2, "dmq_load"),

    # -- Underground Equipment --
    ("dmq_underground",       "Underground Mining Equipment",                  1, None),
    ("dmq_underground_lhd",   "LHD (Load Haul Dump) Loader",                 2, "dmq_underground"),
    ("dmq_underground_truck", "Underground Articulated Haul Truck",           2, "dmq_underground"),
    ("dmq_underground_bolter","Rock Bolt Drilling and Bolting Equipment",     2, "dmq_underground"),
    ("dmq_underground_jumbo", "Drill Jumbo (face development drilling)",      2, "dmq_underground"),
    ("dmq_underground_vent",  "Ventilation Fan and Duct System",              2, "dmq_underground"),

    # -- Processing and Beneficiation Equipment --
    ("dmq_process",           "Processing and Beneficiation Equipment",        1, None),
    ("dmq_process_crush",     "Primary Crusher (jaw, gyratory, cone)",        2, "dmq_process"),
    ("dmq_process_mill",      "Grinding Mill (SAG, ball mill, rod mill)",     2, "dmq_process"),
    ("dmq_process_flotation", "Flotation Cell (sulfide mineral recovery)",    2, "dmq_process"),
    ("dmq_process_heap",      "Heap Leach Pad and Solution Recovery System", 2, "dmq_process"),
    ("dmq_process_smelt",     "Smelter and Roasting Furnace",                 2, "dmq_process"),

    # -- Safety and Support Equipment --
    ("dmq_safety",            "Safety and Support Equipment",                  1, None),
    ("dmq_safety_cap",        "Personnel Carrier and Light Vehicle (LV)",     2, "dmq_safety"),
    ("dmq_safety_refuge",     "Refuge Chamber (underground emergency shelter)", 2, "dmq_safety"),
    ("dmq_safety_gas",        "Gas Detection and Monitoring System",          2, "dmq_safety"),
    ("dmq_safety_water",      "Mine Dewatering Pump System",                  2, "dmq_safety"),
]

_DOMAIN_ROW = (
    "domain_mining_equipment",
    "Mining Equipment Types",
    "Mining equipment and machinery classification - drilling, loading and hauling, "
    "underground equipment, processing, and safety/support equipment",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["21"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific equipment types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_mining_equipment(conn) -> int:
    """Ingest Mining Equipment domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_mining_equipment'), and links NAICS 21 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_mining_equipment",
        "Mining Equipment Types",
        "Mining equipment and machinery classification - drilling, loading and hauling, "
        "underground equipment, processing, and safety/support equipment",
        "1.0",
        "Global",
        "WorldOfTaxanomy",
    )

    await conn.execute(
        """INSERT INTO domain_taxonomy
               (id, name, full_name, authority, url, code_count)
           VALUES ($1, $2, $3, $4, $5, 0)
           ON CONFLICT (id) DO UPDATE SET code_count = 0""",
        *_DOMAIN_ROW,
    )

    parent_codes = {parent for _, _, _, parent in MINING_EQUIPMENT_NODES if parent is not None}

    rows = [
        (
            "domain_mining_equipment",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MINING_EQUIPMENT_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MINING_EQUIPMENT_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_mining_equipment'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_mining_equipment'",
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
            [("naics_2022", code, "domain_mining_equipment", "primary") for code in naics_codes],
        )

    return count
