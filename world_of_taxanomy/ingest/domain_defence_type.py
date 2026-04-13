"""Defence and Security Type domain taxonomy ingester.

Organizes defence and security sector types aligned with
NAICS 928 (National Security) and NAICS 3364 (Aerospace/Defence mfg).

Code prefix: ddf_
Categories: land systems, naval, air/space, cyber/EW, intelligence,
weapons/munitions, force protection, logistics/support.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
DEFENCE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Land Systems --
    ("ddf_land",          "Land Systems",                                           1, None),
    ("ddf_land_armor",    "Armored Fighting Vehicles (tanks, IFV, APC)",           2, "ddf_land"),
    ("ddf_land_arty",     "Artillery and Indirect Fire Systems",                   2, "ddf_land"),
    ("ddf_land_eng",      "Combat Engineering Systems (bridging, obstacle breach)",2, "ddf_land"),

    # -- Naval Systems --
    ("ddf_naval",         "Naval Systems",                                          1, None),
    ("ddf_naval_surface", "Surface Combatants (destroyers, frigates, corvettes)",  2, "ddf_naval"),
    ("ddf_naval_sub",     "Submarines (attack, ballistic missile, conventional)",  2, "ddf_naval"),
    ("ddf_naval_amphi",   "Amphibious and Littoral Systems",                       2, "ddf_naval"),

    # -- Air and Space Systems --
    ("ddf_air",           "Air and Space Systems",                                  1, None),
    ("ddf_air_combat",    "Combat Aircraft (fighters, bombers, attack)",            2, "ddf_air"),
    ("ddf_air_isr",       "ISR Aircraft (surveillance, reconnaissance, AWACS)",    2, "ddf_air"),
    ("ddf_air_uav",       "Military UAV / RPAS (strike, reconnaissance, MALE)",    2, "ddf_air"),

    # -- Cyber and Electronic Warfare --
    ("ddf_cyber",         "Cyber and Electronic Warfare",                           1, None),
    ("ddf_cyber_ops",     "Cyberspace Operations (offensive, defensive, CNO)",     2, "ddf_cyber"),
    ("ddf_cyber_ew",      "Electronic Warfare (jamming, SIGINT, ELINT)",           2, "ddf_cyber"),
    ("ddf_cyber_c4isr",   "C4ISR Systems (command, control, comms, computers)",    2, "ddf_cyber"),

    # -- Missiles and Munitions --
    ("ddf_wpn",           "Missiles and Munitions",                                 1, None),
    ("ddf_wpn_missile",   "Guided Missiles (cruise, ballistic, air-to-air, SAM)",  2, "ddf_wpn"),
    ("ddf_wpn_precision", "Precision-Guided Munitions (JDAM, laser-guided, GPS)",  2, "ddf_wpn"),
    ("ddf_wpn_ammo",      "Conventional Ammunition and Explosives",                2, "ddf_wpn"),

    # -- Force Protection --
    ("ddf_prot",          "Force Protection",                                       1, None),
    ("ddf_prot_armor",    "Personal Armor and Ballistic Protection",               2, "ddf_prot"),
    ("ddf_prot_cbrn",     "CBRN Protection and Detection Systems",                 2, "ddf_prot"),
]

_DOMAIN_ROW = (
    "domain_defence_type",
    "Defence and Security Types",
    "Land systems, naval, air/space, cyber/electronic warfare, missiles, "
    "force protection and military logistics taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 928 (National security), 3364 (Aerospace/defence mfg)
_NAICS_PREFIXES = ["928", "3364"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific defence types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_defence_type(conn) -> int:
    """Ingest Defence and Security Type domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_defence_type'), and links NAICS 928/3364 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_defence_type",
        "Defence and Security Types",
        "Land systems, naval, air/space, cyber/electronic warfare, missiles, "
        "force protection and military logistics taxonomy",
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

    parent_codes = {parent for _, _, _, parent in DEFENCE_NODES if parent is not None}

    rows = [
        (
            "domain_defence_type",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in DEFENCE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(DEFENCE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_defence_type'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_defence_type'",
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
            [("naics_2022", code, "domain_defence_type", "primary") for code in naics_codes],
        )

    return count
