"""New Energy Storage domain taxonomy ingester.

Organizes new energy storage sector types aligned with
NAICS 335 (Electrical equipment), NAICS 3691 (Battery mfg),
and NAICS 2211 (Electric power generation).

Code prefix: des_
Categories: battery chemistries, grid-scale storage, thermal storage,
hydrogen storage, vehicle batteries, storage software.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
STORAGE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Battery Chemistries --
    ("des_batt",            "Battery Chemistries",                                   1, None),
    ("des_batt_liion",      "Lithium-Ion (NMC, LFP, NCA, cylindrical, pouch)",      2, "des_batt"),
    ("des_batt_solid",      "Solid-State Batteries (sulfide, oxide, polymer SSE)",  2, "des_batt"),
    ("des_batt_sodium",     "Sodium-Ion Batteries (hard carbon, NASICON cathode)",  2, "des_batt"),
    ("des_batt_flow",       "Flow Batteries (vanadium redox, zinc-bromine, iron)",  2, "des_batt"),

    # -- Grid-Scale Storage --
    ("des_grid",            "Grid-Scale Energy Storage",                             1, None),
    ("des_grid_bess",       "Battery Energy Storage Systems (utility BESS, front-of-meter)",2, "des_grid"),
    ("des_grid_hydro",      "Pumped Hydroelectric Storage (PSH)",                   2, "des_grid"),
    ("des_grid_caes",       "Compressed Air Energy Storage (CAES, adiabatic CAES)", 2, "des_grid"),

    # -- Thermal Storage --
    ("des_therm",           "Thermal Energy Storage",                                1, None),
    ("des_therm_molten",    "Molten Salt Thermal Storage (CSP, industrial heat)",   2, "des_therm"),
    ("des_therm_ice",       "Ice and Chilled Water Storage (HVAC, district cooling)",2, "des_therm"),
    ("des_therm_pcm",       "Phase Change Materials (PCM) Thermal Storage",         2, "des_therm"),

    # -- Hydrogen Storage --
    ("des_h2",              "Hydrogen Energy Storage",                               1, None),
    ("des_h2_compressed",   "Compressed Gaseous Hydrogen (350/700 bar tanks)",      2, "des_h2"),
    ("des_h2_liquid",       "Liquid Hydrogen Storage and Cryogenic Systems",        2, "des_h2"),
    ("des_h2_hydride",      "Metal Hydride and Chemical Hydrogen Storage",          2, "des_h2"),

    # -- Vehicle Battery Systems --
    ("des_veh",             "Vehicle Battery Systems",                               1, None),
    ("des_veh_passenger",   "Passenger EV Battery Packs (NMC/LFP, cylindrical/pouch)",2, "des_veh"),
    ("des_veh_commercial",  "Commercial Vehicle Battery Systems (trucks, buses)",   2, "des_veh"),
    ("des_veh_ebike",       "E-Bike and Micro-Mobility Batteries",                  2, "des_veh"),

    # -- Storage Software and Management --
    ("des_soft",            "Storage Software and Management",                       1, None),
    ("des_soft_bms",        "Battery Management Systems (BMS)",                     2, "des_soft"),
    ("des_soft_ems",        "Energy Management Systems (EMS) and SCADA",            2, "des_soft"),
    ("des_soft_vpp",        "Virtual Power Plants (VPP) and Grid Dispatch",         2, "des_soft"),
]

_DOMAIN_ROW = (
    "domain_energy_storage",
    "New Energy Storage Types",
    "Battery chemistries, grid-scale storage, thermal storage, "
    "hydrogen storage, vehicle batteries and storage software taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 335 (Electrical equip), 3691 (Battery mfg), 2211 (Electric power)
_NAICS_PREFIXES = ["335", "3691", "2211"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific energy storage types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_energy_storage(conn) -> int:
    """Ingest New Energy Storage domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_energy_storage'), and links NAICS 335/3691/2211 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_energy_storage",
        "New Energy Storage Types",
        "Battery chemistries, grid-scale storage, thermal storage, "
        "hydrogen storage, vehicle batteries and storage software taxonomy",
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

    parent_codes = {parent for _, _, _, parent in STORAGE_NODES if parent is not None}

    rows = [
        (
            "domain_energy_storage",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in STORAGE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(STORAGE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_energy_storage'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_energy_storage'",
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
            [("naics_2022", code, "domain_energy_storage", "primary") for code in naics_codes],
        )

    return count
