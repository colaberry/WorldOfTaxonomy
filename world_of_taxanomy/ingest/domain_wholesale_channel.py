"""Wholesale Trade domain taxonomy ingester.

Wholesale trade taxonomy organizes distribution channels (NAICS 42):
  Distribution Channel (dwc_dist*) - direct, broker, distributor, drop-ship, marketplace
  Fulfillment Method   (dwc_fulfill*) - 1PL through 4PL, cross-dock, cold chain
  Buyer Category       (dwc_buyer*) - retailer, manufacturer, government, foodservice
  Cold Chain           (dwc_cold*) - ambient, refrigerated, frozen, controlled atmosphere

Source: NAICS 42 subsectors + CSCMP (Council of Supply Chain Management Professionals).
Public domain. Hand-coded. Open.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
WHOLESALE_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Distribution Channel category --
    ("dwc_dist",           "Distribution Channel Type",                         1, None),
    ("dwc_dist_direct",    "Direct Sales (manufacturer to end buyer)",         2, "dwc_dist"),
    ("dwc_dist_broker",    "Broker and Agent (commission-based intermediary)", 2, "dwc_dist"),
    ("dwc_dist_distrib",   "Full-Service Distributor (stock and deliver)",     2, "dwc_dist"),
    ("dwc_dist_dropship",  "Drop-Ship (supplier ships direct to customer)",    2, "dwc_dist"),
    ("dwc_dist_market",    "Online Marketplace (B2B platform, e-procurement)", 2, "dwc_dist"),

    # -- Fulfillment Method category --
    ("dwc_fulfill",        "Fulfillment and Logistics Method",                  1, None),
    ("dwc_fulfill_1pl",    "1PL - Private Fleet (own trucks, own staff)",      2, "dwc_fulfill"),
    ("dwc_fulfill_3pl",    "3PL - Third-Party Logistics (outsourced)",         2, "dwc_fulfill"),
    ("dwc_fulfill_4pl",    "4PL - Lead Logistics Provider (orchestration)",   2, "dwc_fulfill"),
    ("dwc_fulfill_xdock",  "Cross-Dock (transit without storage)",             2, "dwc_fulfill"),

    # -- Buyer Category --
    ("dwc_buyer",          "Wholesale Buyer Category",                          1, None),
    ("dwc_buyer_retail",   "Retail and Mass Merchant Buyer",                   2, "dwc_buyer"),
    ("dwc_buyer_mfg",      "Industrial and Manufacturing Buyer",               2, "dwc_buyer"),
    ("dwc_buyer_govt",     "Government and Institutional Buyer",               2, "dwc_buyer"),
    ("dwc_buyer_food",     "Foodservice and Restaurant Buyer",                 2, "dwc_buyer"),

    # -- Cold Chain / Temperature Control --
    ("dwc_cold",           "Temperature and Cold Chain Management",             1, None),
    ("dwc_cold_ambient",   "Ambient (non-refrigerated, dry storage)",          2, "dwc_cold"),
    ("dwc_cold_fresh",     "Refrigerated Fresh (0 to 4 deg C)",                2, "dwc_cold"),
    ("dwc_cold_frozen",    "Frozen (below -18 deg C)",                         2, "dwc_cold"),
    ("dwc_cold_controlled","Controlled Atmosphere (CA storage for produce)",   2, "dwc_cold"),
]

_DOMAIN_ROW = (
    "domain_wholesale_channel",
    "Wholesale Trade Channels",
    "Distribution channel, fulfillment method, buyer category and cold chain taxonomy for NAICS 42",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["42"]


def _determine_level(code: str) -> int:
    """Return level: 1 for top categories, 2 for specific wholesale types."""
    parts = code.split("_")
    if len(parts) == 2:
        return 1
    return 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_wholesale_channel(conn) -> int:
    """Ingest Wholesale Trade Channel domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_wholesale_channel'), and links NAICS 42xxx nodes
    via node_taxonomy_link.

    Returns total wholesale channel node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_wholesale_channel",
        "Wholesale Trade Channels",
        "Distribution channel, fulfillment method, buyer category and cold chain taxonomy for NAICS 42",
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

    parent_codes = {parent for _, _, _, parent in WHOLESALE_NODES if parent is not None}

    rows = [
        (
            "domain_wholesale_channel",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in WHOLESALE_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(WHOLESALE_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_wholesale_channel'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_wholesale_channel'",
        count,
    )

    naics_codes = [
        row["code"]
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE '42%'"
        )
    ]

    await conn.executemany(
        """INSERT INTO node_taxonomy_link
               (system_id, node_code, taxonomy_id, relevance)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
        [("naics_2022", code, "domain_wholesale_channel", "primary") for code in naics_codes],
    )

    return count
