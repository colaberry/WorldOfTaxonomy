"""Manufacturing Industry Vertical Types domain taxonomy ingester.

Manufacturing industry vertical classification - automotive, aerospace, electronics, life sciences, food and beverage, chemical, industrial.

Code prefix: dfpi_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
MFG_INDUSTRY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Automotive and Transportation Equipment --
    ("dfpi_auto", "Automotive and Transportation Equipment", 1, None),
    ("dfpi_auto_oem", "OEM Vehicle Assembly (Tier 1 supply, final assembly)", 2, 'dfpi_auto'),
    ("dfpi_auto_tier2", "Tier 2-3 Automotive Components and Stamping", 2, 'dfpi_auto'),
    ("dfpi_auto_ev", "Electric Vehicle and Battery Pack Manufacturing", 2, 'dfpi_auto'),
    # -- Aerospace and Defense Manufacturing --
    ("dfpi_aero", "Aerospace and Defense Manufacturing", 1, None),
    ("dfpi_aero_civil", "Commercial Aviation Structures and Engines (FAA Part 21)", 2, 'dfpi_aero'),
    ("dfpi_aero_defense", "Defense Systems and Platforms (ITAR controlled)", 2, 'dfpi_aero'),
    ("dfpi_aero_space", "Space and Satellite Hardware Manufacturing", 2, 'dfpi_aero'),
    # -- Electronics and Semiconductor Manufacturing --
    ("dfpi_elec", "Electronics and Semiconductor Manufacturing", 1, None),
    ("dfpi_elec_semi", "Semiconductor Wafer Fab and Packaging", 2, 'dfpi_elec'),
    ("dfpi_elec_pcba", "PCB Assembly and Electronics Manufacturing Services", 2, 'dfpi_elec'),
    ("dfpi_elec_display", "Display and Optoelectronics Manufacturing", 2, 'dfpi_elec'),
    # -- Life Sciences and Medical Devices --
    ("dfpi_life", "Life Sciences and Medical Devices", 1, None),
    ("dfpi_life_implant", "Implantable Medical Devices (FDA Class III)", 2, 'dfpi_life'),
    ("dfpi_life_diag", "Diagnostics and In-Vitro Device Manufacturing (IVD)", 2, 'dfpi_life'),
    ("dfpi_life_pharma", "Pharmaceutical Drug Manufacturing (FDA 21 CFR 210/211)", 2, 'dfpi_life'),
    # -- Food and Beverage Manufacturing --
    ("dfpi_food", "Food and Beverage Manufacturing", 1, None),
    ("dfpi_food_process", "Processed Food and Packaged Goods (FDA FSMA)", 2, 'dfpi_food'),
    ("dfpi_food_bev", "Beverage Manufacturing (beer, spirits, soft drinks)", 2, 'dfpi_food'),
    ("dfpi_food_cold", "Frozen and Refrigerated Food Manufacturing", 2, 'dfpi_food'),
    # -- Chemical and Materials Manufacturing --
    ("dfpi_chem", "Chemical and Materials Manufacturing", 1, None),
    ("dfpi_chem_basic", "Basic Chemicals (industrial chemicals, petrochemicals)", 2, 'dfpi_chem'),
    ("dfpi_chem_specialty", "Specialty Chemicals (adhesives, coatings, catalysts)", 2, 'dfpi_chem'),
    # -- Industrial Equipment and Machinery --
    ("dfpi_indust", "Industrial Equipment and Machinery", 1, None),
    ("dfpi_indust_heavy", "Heavy Industrial Machinery and Machine Tools", 2, 'dfpi_indust'),
    ("dfpi_indust_robot", "Industrial Robots and Automation Equipment", 2, 'dfpi_indust'),
]

_DOMAIN_ROW = (
    "domain_mfg_industry",
    "Manufacturing Industry Vertical Types",
    "Manufacturing industry vertical classification - automotive, aerospace, electronics, life sciences, food and beverage, chemical, industrial",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['31', '32', '33']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_mfg_industry(conn) -> int:
    """Ingest Manufacturing Industry Vertical Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_mfg_industry",
        "Manufacturing Industry Vertical Types",
        "Manufacturing industry vertical classification - automotive, aerospace, electronics, life sciences, food and beverage, chemical, industrial",
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

    parent_codes = {parent for _, _, _, parent in MFG_INDUSTRY_NODES if parent is not None}

    rows = [
        (
            "domain_mfg_industry",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in MFG_INDUSTRY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(MFG_INDUSTRY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_mfg_industry'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_mfg_industry'",
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
            [("naics_2022", code, "domain_mfg_industry", "primary") for code in naics_codes],
        )

    return count
