"""Mining Project Lifecycle Phase domain taxonomy ingester.

Classifies what stage of its operational life a mine is in - orthogonal
to mineral type, extraction method, reserve classification, and equipment.
A copper mine and a gold mine both pass through greenfield exploration,
feasibility, development, production, and eventually closure - different
asset values, regulatory obligations, and workforce compositions at each
stage.

Code prefix: dmlc_
Categories: Exploration and Discovery, Feasibility and Permitting,
Development and Construction, Operations and Production, Care and
Maintenance, Closure and Rehabilitation.

Stakeholders: mining project finance lenders (IFC, export credit agencies),
ESG investors tracking mine lifecycle risk, government permitting agencies,
mine rehabilitation bond administrators, royalty streaming companies.
Source: JORC Code lifecycle phases, IFC Performance Standards on mining,
MAC (Mining Association of Canada) lifecycle guidance. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MINING_LIFECYCLE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Exploration and Discovery --
    ("dmlc_explore",          "Exploration and Discovery Phase",               1, None),
    ("dmlc_explore_grass",    "Grassroots Exploration (early-stage target gen)", 2, "dmlc_explore"),
    ("dmlc_explore_advanced", "Advanced Exploration (drilling, resource estimation)", 2, "dmlc_explore"),
    ("dmlc_explore_scout",    "Scout / Brownfield Near-Mine Exploration",      2, "dmlc_explore"),

    # -- Feasibility and Permitting --
    ("dmlc_feasibility",      "Feasibility and Permitting Phase",              1, None),
    ("dmlc_feasibility_pea",  "Preliminary Economic Assessment (PEA / Scoping)", 2, "dmlc_feasibility"),
    ("dmlc_feasibility_pfs",  "Pre-Feasibility Study (PFS)",                  2, "dmlc_feasibility"),
    ("dmlc_feasibility_dfs",  "Definitive Feasibility Study (DFS / BFS)",     2, "dmlc_feasibility"),
    ("dmlc_feasibility_permit","Environmental Permitting and EIA Process",    2, "dmlc_feasibility"),

    # -- Development and Construction --
    ("dmlc_develop",          "Development and Construction Phase",            1, None),
    ("dmlc_develop_early",    "Early Works and Site Preparation",              2, "dmlc_develop"),
    ("dmlc_develop_build",    "Full Construction (processing plant, infrastructure)", 2, "dmlc_develop"),
    ("dmlc_develop_commiss",  "Commissioning and Systems Integration",        2, "dmlc_develop"),

    # -- Operations and Production --
    ("dmlc_produce",          "Operations and Production Phase",               1, None),
    ("dmlc_produce_ramp",     "Ramp-Up (achieving nameplate capacity)",       2, "dmlc_produce"),
    ("dmlc_produce_steady",   "Steady-State Production",                      2, "dmlc_produce"),
    ("dmlc_produce_expand",   "Mine Expansion (pushback, depth extension)",   2, "dmlc_produce"),
    ("dmlc_produce_sustaining","Sustaining Capital Phase (mature mine)",      2, "dmlc_produce"),

    # -- Care and Maintenance --
    ("dmlc_care",             "Care and Maintenance Phase",                    1, None),
    ("dmlc_care_idle",        "Idle / Temporarily Suspended Operations",      2, "dmlc_care"),
    ("dmlc_care_restart",     "Restart and Reactivation Assessment",          2, "dmlc_care"),

    # -- Closure and Rehabilitation --
    ("dmlc_closure",          "Closure and Rehabilitation Phase",              1, None),
    ("dmlc_closure_plan",     "Mine Closure Planning and Bond Calculation",   2, "dmlc_closure"),
    ("dmlc_closure_decommiss","Active Decommissioning and Demolition",        2, "dmlc_closure"),
    ("dmlc_closure_rehab",    "Land Rehabilitation and Revegetation",         2, "dmlc_closure"),
    ("dmlc_closure_monitor",  "Long-Term Post-Closure Monitoring",            2, "dmlc_closure"),
]

_DOMAIN_ROW = (
    "domain_mining_lifecycle",
    "Mining Project Lifecycle Phase Types",
    "Mining project lifecycle classification - exploration, feasibility, development, "
    "production, care and maintenance, closure and rehabilitation",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["21"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific lifecycle phase types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_mining_lifecycle(conn) -> int:
    """Ingest Mining Project Lifecycle Phase domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_mining_lifecycle'), and links NAICS 21 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_mining_lifecycle",
        "Mining Project Lifecycle Phase Types",
        "Mining project lifecycle classification - exploration, feasibility, development, "
        "production, care and maintenance, closure and rehabilitation",
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

    parent_codes = {parent for _, _, _, parent in MINING_LIFECYCLE_NODES if parent is not None}

    rows = [
        (
            "domain_mining_lifecycle",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MINING_LIFECYCLE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MINING_LIFECYCLE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_mining_lifecycle'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_mining_lifecycle'",
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
            [("naics_2022", code, "domain_mining_lifecycle", "primary") for code in naics_codes],
        )

    return count
