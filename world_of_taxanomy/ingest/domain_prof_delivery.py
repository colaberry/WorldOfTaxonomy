"""Professional Services Delivery Model Types domain taxonomy ingester.

Professional services delivery model classification - on-site, remote, offshore, hybrid, product-led.

Code prefix: dpsdeliv_
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
PROF_DELIVERY_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- On-Site and Embedded Delivery --
    ("dpsdeliv_onsite", "On-Site and Embedded Delivery", 1, None),
    ("dpsdeliv_onsite_embedded", "Long-Term Embedded Engagement (client premises)", 2, 'dpsdeliv_onsite'),
    ("dpsdeliv_onsite_field", "Field and On-Location Delivery (inspections, audit)", 2, 'dpsdeliv_onsite'),
    # -- Remote and Virtual Delivery --
    ("dpsdeliv_remote", "Remote and Virtual Delivery", 1, None),
    ("dpsdeliv_remote_offshore", "Offshore Delivery Center (India, Philippines, LATAM)", 2, 'dpsdeliv_remote'),
    ("dpsdeliv_remote_nearshore", "Nearshore Delivery (Mexico, Canada, Eastern Europe)", 2, 'dpsdeliv_remote'),
    ("dpsdeliv_remote_domestic", "Domestic Remote (US-based, virtual team)", 2, 'dpsdeliv_remote'),
    # -- Hybrid Delivery Model --
    ("dpsdeliv_hybrid", "Hybrid Delivery Model", 1, None),
    ("dpsdeliv_hybrid_agile", "Agile and Sprint-Based Hybrid Teams", 2, 'dpsdeliv_hybrid'),
    ("dpsdeliv_hybrid_pod", "Pod-Based Delivery (blended on/offshore team)", 2, 'dpsdeliv_hybrid'),
    # -- Product-Led and Platform Delivery --
    ("dpsdeliv_product", "Product-Led and Platform Delivery", 1, None),
    ("dpsdeliv_product_saas", "SaaS-Enabled Services (software plus advisory)", 2, 'dpsdeliv_product'),
    ("dpsdeliv_product_self", "Self-Service and Automated Workflow Delivery", 2, 'dpsdeliv_product'),
    ("dpsdeliv_outcome", "Outcome-Based and Managed Services", 1, None),
    ("dpsdeliv_outcome_msp", "Managed Service Provider (MSP) - ongoing ops responsibility", 2, 'dpsdeliv_outcome'),
]

_DOMAIN_ROW = (
    "domain_prof_delivery",
    "Professional Services Delivery Model Types",
    "Professional services delivery model classification - on-site, remote, offshore, hybrid, product-led",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ['54']


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_prof_delivery(conn) -> int:
    """Ingest Professional Services Delivery Model Types.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_prof_delivery",
        "Professional Services Delivery Model Types",
        "Professional services delivery model classification - on-site, remote, offshore, hybrid, product-led",
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

    parent_codes = {parent for _, _, _, parent in PROF_DELIVERY_NODES if parent is not None}

    rows = [
        (
            "domain_prof_delivery",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in PROF_DELIVERY_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(PROF_DELIVERY_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_prof_delivery'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_prof_delivery'",
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
            [("naics_2022", code, "domain_prof_delivery", "primary") for code in naics_codes],
        )

    return count
