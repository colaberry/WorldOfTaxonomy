"""Wholesale Trade Regulatory Compliance Types domain taxonomy ingester.

Wholesale trade regulatory compliance classification - FDA drug supply chain, USDA food safety, EPA chemicals, DEA controlled substances.

Code prefix: dwcreg_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
WHOLESALE_REG_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- FDA Supply Chain and Drug Distribution Compliance --
    ("dwcreg_fda", "FDA Supply Chain and Drug Distribution Compliance", 1, None),
    ("dwcreg_fda_drug", "FDA DSCSA Drug Supply Chain Security Act (serialization, traceability)", 2, 'dwcreg_fda'),
    ("dwcreg_fda_food", "FDA FSMA Sanitary Food Transport Rule", 2, 'dwcreg_fda'),
    ("dwcreg_fda_device", "FDA Medical Device Distribution (UDI, 21 CFR 820)", 2, 'dwcreg_fda'),
    # -- USDA Agricultural Marketing and Food Safety Compliance --
    ("dwcreg_usda", "USDA Agricultural Marketing and Food Safety Compliance", 1, None),
    ("dwcreg_usda_meat", "USDA FSIS Meat and Poultry Distributor Requirements", 2, 'dwcreg_usda'),
    ("dwcreg_usda_ams", "USDA AMS Perishable Agricultural Commodities Act (PACA)", 2, 'dwcreg_usda'),
    # -- EPA Chemical and Hazardous Material Compliance --
    ("dwcreg_epa", "EPA Chemical and Hazardous Material Compliance", 1, None),
    ("dwcreg_epa_tsca", "EPA TSCA Chemical Distribution Requirements", 2, 'dwcreg_epa'),
    ("dwcreg_epa_rcra", "EPA RCRA Hazardous Waste Generator and Transporter", 2, 'dwcreg_epa'),
    # -- DEA Controlled Substance Distribution Compliance --
    ("dwcreg_dea", "DEA Controlled Substance Distribution Compliance", 1, None),
    ("dwcreg_dea_dist", "DEA Schedule II-V Distributor Registration (21 USC 828)", 2, 'dwcreg_dea'),
    ("dwcreg_dea_chem", "DEA Listed Chemical Distribution (precursor chemicals)", 2, 'dwcreg_dea'),
    # -- DOT Hazardous Materials Transportation Compliance --
    ("dwcreg_dot", "DOT Hazardous Materials Transportation Compliance", 1, None),
    ("dwcreg_dot_hm", "DOT 49 CFR HazMat Shipping and Packaging Requirements", 2, 'dwcreg_dot'),
    ("dwcreg_dot_temp", "DOT Temperature-Controlled Food Transport (21 CFR)", 2, 'dwcreg_dot'),
]

_DOMAIN_ROW = (
    "domain_wholesale_regulatory",
    "Wholesale Trade Regulatory Compliance Types",
    "Wholesale trade regulatory compliance classification - FDA drug supply chain, USDA food safety, EPA chemicals, DEA controlled substances",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['42']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_wholesale_regulatory(conn) -> int:
    """Ingest Wholesale Trade Regulatory Compliance Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_wholesale_regulatory",
        "Wholesale Trade Regulatory Compliance Types",
        "Wholesale trade regulatory compliance classification - FDA drug supply chain, USDA food safety, EPA chemicals, DEA controlled substances",
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

    parent_codes = {parent for _, _, _, parent in WHOLESALE_REG_NODES if parent is not None}

    rows = [
        (
            "domain_wholesale_regulatory",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in WHOLESALE_REG_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(WHOLESALE_REG_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_wholesale_regulatory'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_wholesale_regulatory'",
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
            [("naics_2022", code, "domain_wholesale_regulatory", "primary") for code in naics_codes],
        )

    return count
