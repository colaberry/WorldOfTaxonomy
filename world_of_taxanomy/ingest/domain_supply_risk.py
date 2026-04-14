"""Supply Chain Risk and Disruption Category Types domain taxonomy ingester.

Supply chain risk and disruption category classification - supplier risk, geopolitical, weather/climate, cyber, demand, and compliance.

Code prefix: dscrisk_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
SUPPLY_RISK_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Supplier and Sourcing Risk --
    ("dscrisk_supplier", "Supplier and Sourcing Risk", 1, None),
    ("dscrisk_supplier_single", "Single-Source Concentration Risk (sole-source dependency)", 2, 'dscrisk_supplier'),
    ("dscrisk_supplier_financial", "Supplier Financial Distress and Insolvency Risk", 2, 'dscrisk_supplier'),
    ("dscrisk_supplier_quality", "Supplier Quality and Specification Compliance Risk", 2, 'dscrisk_supplier'),
    # -- Geopolitical and Trade Policy Risk --
    ("dscrisk_geo", "Geopolitical and Trade Policy Risk", 1, None),
    ("dscrisk_geo_trade", "Trade War and Tariff Risk (Section 301, 232, AD/CVD)", 2, 'dscrisk_geo'),
    ("dscrisk_geo_sanction", "Sanctions and Export Control Risk (OFAC, BIS EAR)", 2, 'dscrisk_geo'),
    ("dscrisk_geo_conflict", "Regional Conflict and Political Instability Risk", 2, 'dscrisk_geo'),
    # -- Weather, Climate, and Natural Disaster Risk --
    ("dscrisk_weather", "Weather, Climate, and Natural Disaster Risk", 1, None),
    ("dscrisk_weather_hurricane", "Hurricane and Extreme Weather Event Disruption", 2, 'dscrisk_weather'),
    ("dscrisk_weather_drought", "Drought and Water Scarcity Risk (agriculture, energy)", 2, 'dscrisk_weather'),
    ("dscrisk_weather_climate", "Long-Term Climate Risk to Infrastructure and Routes", 2, 'dscrisk_weather'),
    # -- Cybersecurity and Digital Supply Chain Risk --
    ("dscrisk_cyber", "Cybersecurity and Digital Supply Chain Risk", 1, None),
    ("dscrisk_cyber_ransomware", "Ransomware Attack on Logistics or Manufacturing System", 2, 'dscrisk_cyber'),
    ("dscrisk_cyber_software", "Software Supply Chain Attack (SolarWinds, Log4j type)", 2, 'dscrisk_cyber'),
    # -- Demand Volatility and Inventory Risk --
    ("dscrisk_demand", "Demand Volatility and Inventory Risk", 1, None),
    ("dscrisk_demand_bullwhip", "Bullwhip Effect and Forecast Error Risk", 2, 'dscrisk_demand'),
    ("dscrisk_demand_shortage", "Product Shortage and Allocation Risk", 2, 'dscrisk_demand'),
]

_DOMAIN_ROW = (
    "domain_supply_risk",
    "Supply Chain Risk and Disruption Category Types",
    "Supply chain risk and disruption category classification - supplier risk, geopolitical, weather/climate, cyber, demand, and compliance",
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


async def ingest_domain_supply_risk(conn) -> int:
    """Ingest Supply Chain Risk and Disruption Category Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_supply_risk",
        "Supply Chain Risk and Disruption Category Types",
        "Supply chain risk and disruption category classification - supplier risk, geopolitical, weather/climate, cyber, demand, and compliance",
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

    parent_codes = {parent for _, _, _, parent in SUPPLY_RISK_NODES if parent is not None}

    rows = [
        (
            "domain_supply_risk",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in SUPPLY_RISK_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(SUPPLY_RISK_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_supply_risk'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_supply_risk'",
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
            [("naics_2022", code, "domain_supply_risk", "primary") for code in naics_codes],
        )

    return count
