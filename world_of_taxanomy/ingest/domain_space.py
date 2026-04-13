"""Space and Satellite Economy domain taxonomy ingester.

Organizes space and satellite economy sector types aligned with
NAICS 336414 (Guided missile/spacecraft mfg), NAICS 517 (Telecom),
and NAICS 5417 (R&D).

Code prefix: dsp_
Categories: launch vehicles, satellite types, in-orbit services,
ground segment, downstream applications, space tourism.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
SPACE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Launch Vehicles --
    ("dsp_launch",          "Launch Vehicles",                                       1, None),
    ("dsp_launch_small",    "Small Lift Launch (under 2t to LEO - Rocket Lab, ISRO)",2, "dsp_launch"),
    ("dsp_launch_medium",   "Medium Lift Launch (2-20t to LEO - Falcon 9 class)",   2, "dsp_launch"),
    ("dsp_launch_heavy",    "Heavy and Super-Heavy Launch (>20t - Starship, SLS)",  2, "dsp_launch"),

    # -- Satellite Types --
    ("dsp_sat",             "Satellite Types",                                       1, None),
    ("dsp_sat_comms",       "Communications Satellites (GEO/LEO broadband, relay)", 2, "dsp_sat"),
    ("dsp_sat_eo",          "Earth Observation Satellites (optical, SAR, hyperspectral)",2, "dsp_sat"),
    ("dsp_sat_nav",         "Navigation and Positioning Satellites (GPS, Galileo)", 2, "dsp_sat"),
    ("dsp_sat_science",     "Science and Weather Satellites (climate, space weather)",2, "dsp_sat"),

    # -- In-Orbit Services --
    ("dsp_orbit",           "In-Orbit Services",                                     1, None),
    ("dsp_orbit_service",   "Satellite Servicing and Life Extension",                2, "dsp_orbit"),
    ("dsp_orbit_debris",    "Active Debris Removal and Space Sustainability",        2, "dsp_orbit"),
    ("dsp_orbit_mfg",       "In-Space Manufacturing and Assembly",                  2, "dsp_orbit"),

    # -- Ground Segment --
    ("dsp_ground",          "Ground Segment",                                        1, None),
    ("dsp_ground_ttc",      "Telemetry, Tracking and Command (TT&C) Networks",      2, "dsp_ground"),
    ("dsp_ground_gateway",  "Ground Station Gateways and Teleport Services",        2, "dsp_ground"),
    ("dsp_ground_sim",      "Mission Simulation and Ground Support Equipment",      2, "dsp_ground"),

    # -- Downstream Applications --
    ("dsp_down",            "Downstream Applications",                               1, None),
    ("dsp_down_imagery",    "Satellite Imagery Analytics and Geospatial AI",        2, "dsp_down"),
    ("dsp_down_connect",    "Satellite Connectivity Services (broadband, IoT)",     2, "dsp_down"),
    ("dsp_down_pos",        "Position and Navigation Services (precision GNSS)",    2, "dsp_down"),

    # -- Space Tourism --
    ("dsp_tour",            "Space Tourism and Commercial Spaceflight",              1, None),
    ("dsp_tour_sub",        "Suborbital Tourism (Blue Origin, Virgin Galactic)",     2, "dsp_tour"),
    ("dsp_tour_orbital",    "Orbital and Station Stays (Axiom, commercial ISS)",    2, "dsp_tour"),
]

_DOMAIN_ROW = (
    "domain_space",
    "Space and Satellite Economy Types",
    "Launch vehicles, satellite types, in-orbit services, ground segment, "
    "downstream applications and space tourism taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 336414 (Spacecraft mfg), 517 (Telecom), 5417 (R&D)
_NAICS_PREFIXES = ["336414", "517", "5417"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific space/satellite types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_space(conn) -> int:
    """Ingest Space and Satellite Economy domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_space'), and links NAICS 336414/517/5417 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_space",
        "Space and Satellite Economy Types",
        "Launch vehicles, satellite types, in-orbit services, ground segment, "
        "downstream applications and space tourism taxonomy",
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

    parent_codes = {parent for _, _, _, parent in SPACE_NODES if parent is not None}

    rows = [
        (
            "domain_space",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in SPACE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(SPACE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_space'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_space'",
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
            [("naics_2022", code, "domain_space", "primary") for code in naics_codes],
        )

    return count
