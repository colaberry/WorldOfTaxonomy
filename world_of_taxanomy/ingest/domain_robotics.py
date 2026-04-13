"""Autonomous Systems and Robotics domain taxonomy ingester.

Organizes autonomous systems and robotics sector types aligned with
NAICS 333 (Machinery mfg), NAICS 336 (Transportation equipment),
and NAICS 5415 (Computer systems design).

Code prefix: drb_
Categories: industrial robots, collaborative robots, mobile robots,
aerial robots (drones), humanoid robots, surgical robots, autonomous vehicles, robot software.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
ROBOTICS_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Industrial Robots --
    ("drb_indust",          "Industrial Robots",                                     1, None),
    ("drb_indust_weld",     "Welding and Joining Robots",                           2, "drb_indust"),
    ("drb_indust_assemble", "Assembly and Handling Robots (pick-and-place, SCARA)", 2, "drb_indust"),
    ("drb_indust_paint",    "Painting and Coating Robots",                          2, "drb_indust"),

    # -- Collaborative Robots --
    ("drb_cobot",           "Collaborative Robots (Cobots)",                         1, None),
    ("drb_cobot_light",     "Light-Duty Cobots (under 10kg payload)",               2, "drb_cobot"),
    ("drb_cobot_heavy",     "Heavy-Duty Cobots (10kg+ payload, shared workspace)",  2, "drb_cobot"),

    # -- Autonomous Mobile Robots --
    ("drb_amr",             "Autonomous Mobile Robots (AMR/AGV)",                   1, None),
    ("drb_amr_indoor",      "Indoor Navigation AMR (warehouse, factory floor)",     2, "drb_amr"),
    ("drb_amr_outdoor",     "Outdoor Autonomous Ground Vehicles (AGV, delivery)",   2, "drb_amr"),
    ("drb_amr_last",        "Last-Mile Delivery Robots (sidewalk, campus)",         2, "drb_amr"),

    # -- Aerial Robots (Drones) --
    ("drb_drone",           "Aerial Robots and Commercial Drones (UAV/RPAS)",       1, None),
    ("drb_drone_inspect",   "Inspection and Survey Drones (infrastructure, agri)",  2, "drb_drone"),
    ("drb_drone_deliver",   "Delivery and Logistics Drones",                        2, "drb_drone"),
    ("drb_drone_defense",   "Commercial Security and Monitoring UAVs",              2, "drb_drone"),

    # -- Humanoid Robots --
    ("drb_human",           "Humanoid and Social Robots",                            1, None),
    ("drb_human_biped",     "Bipedal Humanoid Robots (Boston Dynamics, Figure AI)", 2, "drb_human"),
    ("drb_human_social",    "Social and Service Robots (Pepper, NAO, Astro)",       2, "drb_human"),

    # -- Surgical Robots --
    ("drb_surg",            "Surgical and Medical Robots",                           1, None),
    ("drb_surg_lap",        "Laparoscopic and Minimally Invasive Surgical Robots",  2, "drb_surg"),
    ("drb_surg_ortho",      "Orthopedic and Spine Surgical Robots",                 2, "drb_surg"),

    # -- Autonomous Vehicles --
    ("drb_av",              "Autonomous Vehicles",                                   1, None),
    ("drb_av_passenger",    "Passenger Autonomous Vehicles (robotaxi, L4/L5)",      2, "drb_av"),
    ("drb_av_freight",      "Autonomous Freight Trucks (highway L4 platooning)",    2, "drb_av"),

    # -- Robot Software and AI --
    ("drb_soft",            "Robot Software and AI",                                 1, None),
    ("drb_soft_ros",        "Robot Operating Systems (ROS 2, middleware)",           2, "drb_soft"),
    ("drb_soft_perception", "Robot Perception (SLAM, vision, LiDAR fusion)",        2, "drb_soft"),
]

_DOMAIN_ROW = (
    "domain_robotics",
    "Autonomous Systems and Robotics Types",
    "Industrial robots, cobots, AMR/AGV, drones, humanoid robots, "
    "surgical robots, autonomous vehicles and robot software taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 333 (Machinery mfg), 336 (Transportation equip), 5415 (Computer design)
_NAICS_PREFIXES = ["333", "336", "5415"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific robotics types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_robotics(conn) -> int:
    """Ingest Autonomous Systems and Robotics domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_robotics'), and links NAICS 333/336/5415 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_robotics",
        "Autonomous Systems and Robotics Types",
        "Industrial robots, cobots, AMR/AGV, drones, humanoid robots, "
        "surgical robots, autonomous vehicles and robot software taxonomy",
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

    parent_codes = {parent for _, _, _, parent in ROBOTICS_NODES if parent is not None}

    rows = [
        (
            "domain_robotics",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in ROBOTICS_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(ROBOTICS_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_robotics'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_robotics'",
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
            [("naics_2022", code, "domain_robotics", "primary") for code in naics_codes],
        )

    return count
