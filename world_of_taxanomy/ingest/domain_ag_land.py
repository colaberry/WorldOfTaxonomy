"""Agricultural Land, Soil, and Climate Classification domain taxonomy ingester.

Classifies the physical environment where farming occurs - orthogonal to
what's grown, how it's grown, what equipment is used, and what inputs are
applied. The same farming method applied to Class I irrigated bottomland
in the Central Valley produces very differently than on Class VI dryland
in the Great Plains.

Code prefix: daln_ (ag land - avoids collision with dal_ from domain_ag_livestock)
Categories: USDA Land Capability Class, Major Agricultural Region and Growing
Zone, Soil Type, Water Availability and Hydrology, Climate and Temperature Zone,
Land Use and Tenure Classification.

Stakeholders: USDA NRCS soil scientists, FSA farm records administrators,
ag lenders valuing farmland, carbon credit registries, precision ag platforms
doing field-level analytics, insurance underwriters setting premium zones.
Source: USDA NRCS Land Capability Classification, USDA ERS Agricultural
Resource Management Survey, USDA Plant Hardiness Zone Map. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_LAND_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- USDA Land Capability Classification --
    ("daln_cap",              "USDA Land Capability Classification",                  1, None),
    ("daln_cap_1",            "Class I - Excellent, Few Limitations",                2, "daln_cap"),
    ("daln_cap_2",            "Class II - Good, Moderate Limitations",               2, "daln_cap"),
    ("daln_cap_3",            "Class III - Moderately Good, Severe Limitations",     2, "daln_cap"),
    ("daln_cap_4",            "Class IV - Fair, Very Severe Limitations",            2, "daln_cap"),
    ("daln_cap_56",           "Classes V-VI - Limited Cropland Use",                 2, "daln_cap"),
    ("daln_cap_78",           "Classes VII-VIII - Non-Cropland (range, forest)",     2, "daln_cap"),

    # -- Major Agricultural Region and Growing Zone --
    ("daln_region",           "Major Agricultural Region and Growing Zone",           1, None),
    ("daln_region_corn",      "Corn Belt (IA, IL, IN, OH, MN, SD)",                  2, "daln_region"),
    ("daln_region_plains",    "Great Plains (KS, NE, ND, TX Panhandle)",             2, "daln_region"),
    ("daln_region_south",     "Southeast and Delta (MS, AR, LA, AL cotton and rice)", 2, "daln_region"),
    ("daln_region_west",      "Western Irrigated (CA, WA, ID, AZ specialty crops)",  2, "daln_region"),
    ("daln_region_lake",      "Lake States (MI, WI, MN - dairy, vegetables)",        2, "daln_region"),
    ("daln_region_appala",    "Appalachian (VA, NC, KY - tobacco, burley)",          2, "daln_region"),

    # -- Soil Type --
    ("daln_soil",             "Soil Type and Texture Class",                          1, None),
    ("daln_soil_clay",        "Clay and Clay Loam (high water retention)",            2, "daln_soil"),
    ("daln_soil_silt",        "Silt and Silt Loam (loess deposits, high productivity)", 2, "daln_soil"),
    ("daln_soil_sand",        "Sandy and Sandy Loam (low retention, irrigation req)", 2, "daln_soil"),
    ("daln_soil_muck",        "Organic and Muck Soils (histosols, high vegetable use)", 2, "daln_soil"),
    ("daln_soil_rocky",       "Rocky and Shallow Soils (limited tillage depth)",     2, "daln_soil"),

    # -- Water Availability and Hydrology --
    ("daln_water",            "Water Availability and Hydrology",                     1, None),
    ("daln_water_irrig",      "Irrigated Farmland (surface or groundwater applied)", 2, "daln_water"),
    ("daln_water_dryland",    "Dryland / Rainfed (dependent on precipitation only)", 2, "daln_water"),
    ("daln_water_tile",       "Tile-Drained Cropland (subsurface drainage installed)", 2, "daln_water"),
    ("daln_water_flood",      "Floodplain and Hydric (seasonal inundation risk)",    2, "daln_water"),

    # -- Climate and Temperature Zone --
    ("daln_climate",          "Climate and Temperature Zone",                          1, None),
    ("daln_climate_humid",    "Humid Continental (freeze-thaw cycle, adequate rain)", 2, "daln_climate"),
    ("daln_climate_semi",     "Semi-Arid and Sub-Humid (less than 20 in/year rain)", 2, "daln_climate"),
    ("daln_climate_med",      "Mediterranean and Dry-Summer (CA Central Valley)",    2, "daln_climate"),
    ("daln_climate_trop",     "Subtropical and Tropical (FL, HI, PR - frost-free)",  2, "daln_climate"),

    # -- Land Use and Tenure --
    ("daln_tenure",           "Land Use and Tenure Classification",                   1, None),
    ("daln_tenure_owned",     "Owner-Operated Farmland",                             2, "daln_tenure"),
    ("daln_tenure_cash",      "Cash Rent Farmland (fixed annual rent per acre)",     2, "daln_tenure"),
    ("daln_tenure_share",     "Crop Share Farmland (landlord shares output)",        2, "daln_tenure"),
    ("daln_tenure_crp",       "Conservation Reserve Program (CRP) Enrolled Land",   2, "daln_tenure"),
]

_DOMAIN_ROW = (
    "domain_ag_land",
    "Agricultural Land and Soil Classification Types",
    "Agricultural land, soil, and climate classification - USDA capability class, "
    "growing region, soil type, water availability, climate zone, and land tenure",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific land/soil classification types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_land(conn) -> int:
    """Ingest Agricultural Land and Soil Classification domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_land'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_land",
        "Agricultural Land and Soil Classification Types",
        "Agricultural land, soil, and climate classification - USDA capability class, "
        "growing region, soil type, water availability, climate zone, and land tenure",
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

    parent_codes = {parent for _, _, _, parent in AG_LAND_NODES if parent is not None}

    rows = [
        (
            "domain_ag_land",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_LAND_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_LAND_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_land'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_land'",
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
            [("naics_2022", code, "domain_ag_land", "primary") for code in naics_codes],
        )

    return count
