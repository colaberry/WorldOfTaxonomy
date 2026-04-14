"""Utility Infrastructure Asset Types domain taxonomy ingester.

Classifies the physical capital assets that utilities own and operate -
orthogonal to energy source and grid region. A gas-fired peaker plant, a
wind farm, and a hydroelectric dam all involve the same transmission line
asset types; a coal plant and a solar farm both connect through the same
distribution transformer and substation equipment.

Code prefix: duia_
Categories: Generation Assets, Transmission Infrastructure, Distribution
Infrastructure, Customer Metering and Interface, Storage and Flexibility
Assets.

Stakeholders: utility asset managers, FERC AFUDC capital tracking, state PUC
rate base proceedings, utility M&A due diligence teams, grid reliability
planners (NERC TPL standards), insurance underwriters.
Source: FERC USOA (Uniform System of Accounts) plant accounts, NERC transmission
planning standards, IEEE distribution equipment standards. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
UTIL_ASSET_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Generation Assets --
    ("duia_gen",             "Generation Assets",                               1, None),
    ("duia_gen_plant",       "Central Station Power Plant (thermal, nuclear, hydro)", 2, "duia_gen"),
    ("duia_gen_vre",         "Variable Renewable Generation Plant (solar, wind)", 2, "duia_gen"),
    ("duia_gen_peaker",      "Peaker and Combustion Turbine Plant",            2, "duia_gen"),
    ("duia_gen_dist",        "Distributed Generation Unit (DG - behind meter)", 2, "duia_gen"),

    # -- Transmission Infrastructure --
    ("duia_trans",           "Transmission Infrastructure",                     1, None),
    ("duia_trans_line",      "Transmission Line (overhead and underground)",   2, "duia_trans"),
    ("duia_trans_sub",       "Transmission Substation (step-up/step-down)",    2, "duia_trans"),
    ("duia_trans_hvdc",      "HVDC (High Voltage DC) Transmission System",    2, "duia_trans"),
    ("duia_trans_control",   "Energy Management System and Control Center",    2, "duia_trans"),

    # -- Distribution Infrastructure --
    ("duia_dist",            "Distribution Infrastructure",                     1, None),
    ("duia_dist_line",       "Distribution Line (overhead and underground)",   2, "duia_dist"),
    ("duia_dist_xfmr",       "Distribution Transformer (pad-mount, pole-mount)", 2, "duia_dist"),
    ("duia_dist_switch",     "Distribution Switching Equipment (recloser, switch)", 2, "duia_dist"),
    ("duia_dist_scada",      "Distribution SCADA and Automation (DMS, ADMS)", 2, "duia_dist"),

    # -- Customer Metering and Interface --
    ("duia_meter",           "Customer Metering and Interface Equipment",       1, None),
    ("duia_meter_ami",       "Advanced Metering Infrastructure (AMI / Smart Meter)", 2, "duia_meter"),
    ("duia_meter_legacy",    "Legacy Electromechanical Meter",                 2, "duia_meter"),
    ("duia_meter_comm",      "Meter Communication Network (RF mesh, PLC, LTE)", 2, "duia_meter"),
    ("duia_meter_mdms",      "Meter Data Management System (MDMS)",            2, "duia_meter"),

    # -- Storage and Flexibility Assets --
    ("duia_storage",         "Storage and Flexibility Assets",                  1, None),
    ("duia_storage_bess",    "Battery Energy Storage System (BESS) - utility", 2, "duia_storage"),
    ("duia_storage_pumped",  "Pumped Hydro Storage Facility",                  2, "duia_storage"),
    ("duia_storage_caes",    "Compressed Air Energy Storage (CAES)",           2, "duia_storage"),
    ("duia_storage_dr",      "Demand Response and Virtual Power Plant (VPP)",  2, "duia_storage"),
]

_DOMAIN_ROW = (
    "domain_util_asset",
    "Utility Infrastructure Asset Types",
    "Utility infrastructure asset classification - generation, transmission, "
    "distribution, customer metering, and storage/flexibility assets",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["22"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific asset types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_util_asset(conn) -> int:
    """Ingest Utility Infrastructure Asset Types domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_util_asset'), and links NAICS 22 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_util_asset",
        "Utility Infrastructure Asset Types",
        "Utility infrastructure asset classification - generation, transmission, "
        "distribution, customer metering, and storage/flexibility assets",
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

    parent_codes = {parent for _, _, _, parent in UTIL_ASSET_NODES if parent is not None}

    rows = [
        (
            "domain_util_asset",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in UTIL_ASSET_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(UTIL_ASSET_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_util_asset'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_util_asset'",
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
            [("naics_2022", code, "domain_util_asset", "primary") for code in naics_codes],
        )

    return count
