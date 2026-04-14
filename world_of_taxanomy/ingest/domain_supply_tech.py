"""Supply Chain Technology Platform Types domain taxonomy ingester.

Supply chain technology and digital platform classification - TMS, WMS, OMS, visibility, procurement, planning.

Code prefix: dsctech_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
SUPPLY_TECH_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Transportation Management Systems (TMS) --
    ("dsctech_tms", "Transportation Management Systems (TMS)", 1, None),
    ("dsctech_tms_cloud", "Cloud TMS (MercuryGate, Oracle TMS, SAP TM)", 2, 'dsctech_tms'),
    ("dsctech_tms_freight", "Freight Brokerage Platform (Echo, C.H. Robinson Navisphere)", 2, 'dsctech_tms'),
    ("dsctech_tms_lsp", "4PL / Managed TMS Service Platform", 2, 'dsctech_tms'),
    # -- Warehouse Management Systems (WMS) --
    ("dsctech_wms", "Warehouse Management Systems (WMS)", 1, None),
    ("dsctech_wms_tier1", "Tier 1 WMS (Manhattan Associates, Blue Yonder)", 2, 'dsctech_wms'),
    ("dsctech_wms_robot", "Robotics-Integrated WMS (Autostore, Geek+, Locus)", 2, 'dsctech_wms'),
    # -- Order Management and Commerce Systems (OMS) --
    ("dsctech_oms", "Order Management and Commerce Systems (OMS)", 1, None),
    ("dsctech_oms_cloud", "Cloud OMS / Unified Commerce (Salesforce OMS, Fluent)", 2, 'dsctech_oms'),
    ("dsctech_oms_erp", "ERP-Integrated Order Management (SAP ERP, Oracle, NetSuite)", 2, 'dsctech_oms'),
    # -- Real-Time Visibility and Track-and-Trace Platforms --
    ("dsctech_visibility", "Real-Time Visibility and Track-and-Trace Platforms", 1, None),
    ("dsctech_visibility_realtime", "Real-Time Freight Visibility (project44, FourKites)", 2, 'dsctech_visibility'),
    ("dsctech_visibility_iot", "IoT and Sensor-Based Supply Chain Monitoring", 2, 'dsctech_visibility'),
    # -- Supply Chain Planning and S&OP Platforms --
    ("dsctech_plan", "Supply Chain Planning and S&OP Platforms", 1, None),
    ("dsctech_plan_demand", "Demand Planning and Forecasting (o9, Kinaxis, Blue Yonder)", 2, 'dsctech_plan'),
    ("dsctech_plan_inv", "Inventory Optimization and Multi-Echelon Planning", 2, 'dsctech_plan'),
    # -- Procurement and Sourcing Technology --
    ("dsctech_procure", "Procurement and Sourcing Technology", 1, None),
    ("dsctech_procure_esource", "E-Sourcing and Strategic Sourcing Platform (Ariba, Ivalua)", 2, 'dsctech_procure'),
    ("dsctech_procure_p2p", "Procure-to-Pay (P2P) Platform (Coupa, Jaggaer)", 2, 'dsctech_procure'),
]

_DOMAIN_ROW = (
    "domain_supply_tech",
    "Supply Chain Technology Platform Types",
    "Supply chain technology and digital platform classification - TMS, WMS, OMS, visibility, procurement, planning",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['42', '48', '49']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_supply_tech(conn) -> int:
    """Ingest Supply Chain Technology Platform Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_supply_tech",
        "Supply Chain Technology Platform Types",
        "Supply chain technology and digital platform classification - TMS, WMS, OMS, visibility, procurement, planning",
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

    parent_codes = {parent for _, _, _, parent in SUPPLY_TECH_NODES if parent is not None}

    rows = [
        (
            "domain_supply_tech",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in SUPPLY_TECH_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(SUPPLY_TECH_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_supply_tech'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_supply_tech'",
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
            [("naics_2022", code, "domain_supply_tech", "primary") for code in naics_codes],
        )

    return count
