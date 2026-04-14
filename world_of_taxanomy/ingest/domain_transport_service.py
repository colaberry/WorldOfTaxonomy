"""Transportation Service Type Classification domain taxonomy ingester.

Transportation service type classification - scheduled, charter, cargo-only, passenger, on-demand.

Code prefix: dtsvc_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
TRANSPORT_SERVICE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Scheduled Commercial Service --
    ("dtsvc_scheduled", "Scheduled Commercial Service", 1, None),
    ("dtsvc_scheduled_airline", "Scheduled Commercial Airline (FAR Part 121)", 2, 'dtsvc_scheduled'),
    ("dtsvc_scheduled_rail", "Scheduled Intercity and Commuter Rail", 2, 'dtsvc_scheduled'),
    ("dtsvc_scheduled_ferry", "Scheduled Ferry and Water Passenger Service", 2, 'dtsvc_scheduled'),
    # -- Charter and Non-Scheduled Service --
    ("dtsvc_charter", "Charter and Non-Scheduled Service", 1, None),
    ("dtsvc_charter_air", "Air Charter (FAR Part 135, on-demand air taxi)", 2, 'dtsvc_charter'),
    ("dtsvc_charter_bus", "Motor Coach Charter and Tour Bus", 2, 'dtsvc_charter'),
    ("dtsvc_charter_vessel", "Private Vessel Charter (yacht, cruise charter)", 2, 'dtsvc_charter'),
    # -- Cargo and Freight-Only Service --
    ("dtsvc_cargo", "Cargo and Freight-Only Service", 1, None),
    ("dtsvc_cargo_freight", "Air Cargo Carrier (freighter, belly cargo)", 2, 'dtsvc_cargo'),
    ("dtsvc_cargo_rail_frt", "Rail Freight (Class I, II, III railroad)", 2, 'dtsvc_cargo'),
    ("dtsvc_cargo_ocean", "Ocean Freight (container ship, bulk, tanker)", 2, 'dtsvc_cargo'),
    # -- On-Demand and Rideshare Service --
    ("dtsvc_ondemand", "On-Demand and Rideshare Service", 1, None),
    ("dtsvc_ondemand_tnc", "TNC (Transportation Network Company) Rideshare", 2, 'dtsvc_ondemand'),
    ("dtsvc_ondemand_micro", "Micromobility (e-scooter, e-bike, shared)", 2, 'dtsvc_ondemand'),
    ("dtsvc_ondemand_auto", "Autonomous Ride-Hail (SAE Level 4 commercial)", 2, 'dtsvc_ondemand'),
    # -- Government and Special Purpose Service --
    ("dtsvc_govt", "Government and Special Purpose Service", 1, None),
    ("dtsvc_govt_transit", "Public Transit (urban bus, light rail, subway)", 2, 'dtsvc_govt'),
    ("dtsvc_govt_school", "School Bus and Student Transportation", 2, 'dtsvc_govt'),
]

_DOMAIN_ROW = (
    "domain_transport_service",
    "Transportation Service Type Classification",
    "Transportation service type classification - scheduled, charter, cargo-only, passenger, on-demand",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['48', '49']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_transport_service(conn) -> int:
    """Ingest Transportation Service Type Classification.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_transport_service",
        "Transportation Service Type Classification",
        "Transportation service type classification - scheduled, charter, cargo-only, passenger, on-demand",
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

    parent_codes = {parent for _, _, _, parent in TRANSPORT_SERVICE_NODES if parent is not None}

    rows = [
        (
            "domain_transport_service",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in TRANSPORT_SERVICE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(TRANSPORT_SERVICE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_transport_service'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_transport_service'",
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
            [("naics_2022", code, "domain_transport_service", "primary") for code in naics_codes],
        )

    return count
