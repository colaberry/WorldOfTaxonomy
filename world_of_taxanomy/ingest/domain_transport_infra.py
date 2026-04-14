"""Transportation Infrastructure and Terminal Types domain taxonomy ingester.

Transportation infrastructure and terminal facility classification - airports, seaports, rail yards, intermodal, pipeline.

Code prefix: dtinfra_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
TRANSPORT_INFRA_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Airport and Air Traffic Infrastructure --
    ("dtinfra_airport", "Airport and Air Traffic Infrastructure", 1, None),
    ("dtinfra_airport_hub", "Commercial Service Hub Airport (Enplanements > 10k)", 2, 'dtinfra_airport'),
    ("dtinfra_airport_regional", "Regional and Non-Hub Commercial Airport", 2, 'dtinfra_airport'),
    ("dtinfra_airport_cargo", "Cargo Airport (FedEx Memphis, UPS Louisville hub)", 2, 'dtinfra_airport'),
    # -- Seaport and Marine Terminal --
    ("dtinfra_seaport", "Seaport and Marine Terminal", 1, None),
    ("dtinfra_seaport_container", "Container Port (TEU-based, ship-to-shore cranes)", 2, 'dtinfra_seaport'),
    ("dtinfra_seaport_bulk", "Bulk Cargo Terminal (dry bulk, liquid bulk, ro-ro)", 2, 'dtinfra_seaport'),
    ("dtinfra_seaport_cruise", "Cruise Terminal and Passenger Marine Facility", 2, 'dtinfra_seaport'),
    # -- Rail Yard and Terminal Infrastructure --
    ("dtinfra_rail", "Rail Yard and Terminal Infrastructure", 1, None),
    ("dtinfra_rail_class", "Class I Railroad Classification Yard", 2, 'dtinfra_rail'),
    ("dtinfra_rail_intermodal", "Intermodal Rail Ramp (TOFC, COFC transfer)", 2, 'dtinfra_rail'),
    ("dtinfra_rail_passenger", "Passenger Rail Station (Amtrak, commuter)", 2, 'dtinfra_rail'),
    # -- Intermodal Logistics Center --
    ("dtinfra_intermodal", "Intermodal Logistics Center", 1, None),
    ("dtinfra_intermodal_dc", "Inland Port and Distribution Center", 2, 'dtinfra_intermodal'),
    ("dtinfra_intermodal_ftz", "Foreign Trade Zone (FTZ) Facility", 2, 'dtinfra_intermodal'),
    # -- Pipeline Infrastructure --
    ("dtinfra_pipeline", "Pipeline Infrastructure", 1, None),
    ("dtinfra_pipeline_crude", "Crude Oil Pipeline System (gathering, trunk)", 2, 'dtinfra_pipeline'),
    ("dtinfra_pipeline_gas", "Natural Gas Transmission Pipeline and Compressor", 2, 'dtinfra_pipeline'),
    ("dtinfra_pipeline_products", "Refined Products Pipeline (Colonial, Explorer)", 2, 'dtinfra_pipeline'),
]

_DOMAIN_ROW = (
    "domain_transport_infra",
    "Transportation Infrastructure and Terminal Types",
    "Transportation infrastructure and terminal facility classification - airports, seaports, rail yards, intermodal, pipeline",
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


async def ingest_domain_transport_infra(conn) -> int:
    """Ingest Transportation Infrastructure and Terminal Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_transport_infra",
        "Transportation Infrastructure and Terminal Types",
        "Transportation infrastructure and terminal facility classification - airports, seaports, rail yards, intermodal, pipeline",
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

    parent_codes = {parent for _, _, _, parent in TRANSPORT_INFRA_NODES if parent is not None}

    rows = [
        (
            "domain_transport_infra",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in TRANSPORT_INFRA_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(TRANSPORT_INFRA_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_transport_infra'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_transport_infra'",
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
            [("naics_2022", code, "domain_transport_infra", "primary") for code in naics_codes],
        )

    return count
