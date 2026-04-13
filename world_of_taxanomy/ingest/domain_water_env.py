"""Water and Environment domain taxonomy ingester.

Organizes water and environmental sector types aligned with
NAICS 2213 (Water/Sewage utilities), NAICS 5622 (Waste treatment),
and NAICS 5416 (Environmental consulting).

Code prefix: dwe_
Categories: water treatment, distribution, wastewater, stormwater,
groundwater, desalination, water quality, environmental services.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
WATER_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Water Treatment --
    ("dwe_treat",         "Water Treatment",                                        1, None),
    ("dwe_treat_drink",   "Drinking Water Treatment (coagulation, filtration, UV)", 2, "dwe_treat"),
    ("dwe_treat_disinfect","Disinfection Systems (chlorination, ozonation, UV)",    2, "dwe_treat"),
    ("dwe_treat_softening","Water Softening and Ion Exchange",                      2, "dwe_treat"),

    # -- Water Distribution --
    ("dwe_dist",          "Water Distribution Infrastructure",                      1, None),
    ("dwe_dist_pipe",     "Pipe Networks and Mains (pressurized distribution)",     2, "dwe_dist"),
    ("dwe_dist_pump",     "Pumping Stations and Pressure Management",              2, "dwe_dist"),
    ("dwe_dist_storage",  "Water Storage (tanks, reservoirs, towers)",             2, "dwe_dist"),

    # -- Wastewater Management --
    ("dwe_ww",            "Wastewater Management",                                  1, None),
    ("dwe_ww_collect",    "Wastewater Collection (sewers, lift stations)",          2, "dwe_ww"),
    ("dwe_ww_treat",      "Wastewater Treatment (primary, secondary, tertiary)",   2, "dwe_ww"),
    ("dwe_ww_reuse",      "Water Reclamation and Reuse (recycled water, NEWater)",  2, "dwe_ww"),

    # -- Stormwater and Flood Management --
    ("dwe_storm",         "Stormwater and Flood Management",                        1, None),
    ("dwe_storm_infra",   "Stormwater Infrastructure (retention ponds, bioswales)", 2, "dwe_storm"),
    ("dwe_storm_flood",   "Flood Control Systems (levees, gates, pumps)",           2, "dwe_storm"),

    # -- Groundwater Management --
    ("dwe_gw",            "Groundwater Management",                                 1, None),
    ("dwe_gw_aquifer",    "Aquifer Management and Recharge",                       2, "dwe_gw"),
    ("dwe_gw_well",       "Well Drilling and Monitoring",                          2, "dwe_gw"),

    # -- Desalination --
    ("dwe_desal",         "Desalination",                                           1, None),
    ("dwe_desal_ro",      "Reverse Osmosis Desalination (seawater, brackish)",      2, "dwe_desal"),
    ("dwe_desal_therm",   "Thermal Desalination (MSF, MED, vapor compression)",    2, "dwe_desal"),

    # -- Water Quality and Monitoring --
    ("dwe_qual",          "Water Quality and Monitoring",                           1, None),
    ("dwe_qual_test",     "Water Quality Testing and Analysis",                    2, "dwe_qual"),
    ("dwe_qual_comply",   "Regulatory Compliance and Reporting (EPA, WHO standards)",2, "dwe_qual"),

    # -- Environmental Services --
    ("dwe_env",           "Environmental Services",                                 1, None),
    ("dwe_env_remed",     "Environmental Remediation (soil, groundwater cleanup)",  2, "dwe_env"),
    ("dwe_env_assess",    "Environmental Impact Assessment and Consulting",         2, "dwe_env"),
    ("dwe_env_waste",     "Hazardous Waste Treatment and Disposal",                2, "dwe_env"),
]

_DOMAIN_ROW = (
    "domain_water_env",
    "Water and Environment Types",
    "Water treatment, distribution, wastewater, stormwater, groundwater, "
    "desalination, water quality and environmental services taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 2213 (Water/sewage), 5622 (Waste treatment), 5416 (Env consulting)
_NAICS_PREFIXES = ["2213", "5622", "5416"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific water/env types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_water_env(conn) -> int:
    """Ingest Water and Environment domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_water_env'), and links NAICS 2213/5622/5416 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_water_env",
        "Water and Environment Types",
        "Water treatment, distribution, wastewater, stormwater, groundwater, "
        "desalination, water quality and environmental services taxonomy",
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

    parent_codes = {parent for _, _, _, parent in WATER_NODES if parent is not None}

    rows = [
        (
            "domain_water_env",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in WATER_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(WATER_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_water_env'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_water_env'",
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
            [("naics_2022", code, "domain_water_env", "primary") for code in naics_codes],
        )

    return count
