"""Climate Technology domain taxonomy ingester.

Organizes climate technology sector types aligned with
NAICS 2211 (Electric power generation), NAICS 3353 (Electrical equipment),
and NAICS 5417 (R&D).

Code prefix: dct_
Categories: solar, wind, green hydrogen, carbon capture, carbon markets,
electric vehicles, grid modernization, building efficiency.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
CLIMATE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Solar Energy --
    ("dct_solar",           "Solar Energy",                                          1, None),
    ("dct_solar_pv",        "Solar Photovoltaic (utility, commercial, residential)", 2, "dct_solar"),
    ("dct_solar_csp",       "Concentrated Solar Power (parabolic trough, tower)",   2, "dct_solar"),
    ("dct_solar_bipv",      "Building-Integrated PV and Agrivoltaics",              2, "dct_solar"),

    # -- Wind Energy --
    ("dct_wind",            "Wind Energy",                                           1, None),
    ("dct_wind_onshore",    "Onshore Wind (utility-scale turbines)",                2, "dct_wind"),
    ("dct_wind_offshore",   "Offshore Wind (fixed and floating foundations)",        2, "dct_wind"),
    ("dct_wind_small",      "Small and Distributed Wind",                           2, "dct_wind"),

    # -- Green Hydrogen --
    ("dct_h2",              "Green Hydrogen",                                        1, None),
    ("dct_h2_electro",      "Electrolysis (PEM, alkaline, solid oxide)",            2, "dct_h2"),
    ("dct_h2_store",        "Hydrogen Storage and Transport (compressed, liquid)",  2, "dct_h2"),
    ("dct_h2_fuel",         "Fuel Cells and Power-to-Gas",                          2, "dct_h2"),

    # -- Carbon Capture, Utilization and Storage --
    ("dct_ccs",             "Carbon Capture, Utilization and Storage (CCUS)",       1, None),
    ("dct_ccs_point",       "Point Source Carbon Capture (industrial flue gas)",    2, "dct_ccs"),
    ("dct_ccs_dac",         "Direct Air Capture (DAC) and BECCS",                  2, "dct_ccs"),
    ("dct_ccs_util",        "Carbon Utilization (e-fuels, CO2 to chemicals)",       2, "dct_ccs"),

    # -- Carbon Markets --
    ("dct_carbon",          "Carbon Markets and Climate Finance",                    1, None),
    ("dct_carbon_comply",   "Compliance Carbon Markets (EU ETS, RGGI, CCA)",        2, "dct_carbon"),
    ("dct_carbon_vol",      "Voluntary Carbon Markets and Offsets (VCS, Gold Std)", 2, "dct_carbon"),
    ("dct_carbon_mrv",      "MRV Systems (monitoring, reporting, verification)",    2, "dct_carbon"),

    # -- Electric Vehicles --
    ("dct_ev",              "Electric Vehicles",                                     1, None),
    ("dct_ev_passenger",    "Passenger EVs (BEV, PHEV, range-extender)",            2, "dct_ev"),
    ("dct_ev_commercial",   "Commercial EVs (e-trucks, e-buses, last-mile)",        2, "dct_ev"),
    ("dct_ev_charging",     "EV Charging Infrastructure (Level 2, DCFC, V2G)",      2, "dct_ev"),

    # -- Grid Modernization --
    ("dct_grid",            "Grid Modernization",                                    1, None),
    ("dct_grid_smart",      "Smart Grid and Advanced Metering Infrastructure (AMI)", 2, "dct_grid"),
    ("dct_grid_dr",         "Demand Response and Virtual Power Plants (VPP)",        2, "dct_grid"),

    # -- Building Efficiency --
    ("dct_bldg",            "Building Efficiency and Decarbonization",               1, None),
    ("dct_bldg_retrofit",   "Building Retrofits (insulation, heat pumps, glazing)", 2, "dct_bldg"),
    ("dct_bldg_smart",      "Smart Buildings and Energy Management Systems (EMS)",  2, "dct_bldg"),
]

_DOMAIN_ROW = (
    "domain_climate_tech",
    "Climate Technology Types",
    "Solar, wind, green hydrogen, CCUS, carbon markets, electric vehicles, "
    "grid modernization and building efficiency taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 2211 (Power generation), 3353 (Electrical equip), 5417 (R&D)
_NAICS_PREFIXES = ["2211", "3353", "5417"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific climate tech types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_climate_tech(conn) -> int:
    """Ingest Climate Technology domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_climate_tech'), and links NAICS 2211/3353/5417 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_climate_tech",
        "Climate Technology Types",
        "Solar, wind, green hydrogen, CCUS, carbon markets, electric vehicles, "
        "grid modernization and building efficiency taxonomy",
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

    parent_codes = {parent for _, _, _, parent in CLIMATE_NODES if parent is not None}

    rows = [
        (
            "domain_climate_tech",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in CLIMATE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(CLIMATE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_climate_tech'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_climate_tech'",
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
            [("naics_2022", code, "domain_climate_tech", "primary") for code in naics_codes],
        )

    return count
