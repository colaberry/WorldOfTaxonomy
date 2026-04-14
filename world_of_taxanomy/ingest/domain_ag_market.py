"""Agricultural Market Channel and Sales Type domain taxonomy ingester.

Classifies WHERE farm output is sold - orthogonal to crop type, livestock,
farming method, equipment, inputs, and farm business structure. The same
corn bushel from the same family farm with the same equipment and inputs
can go to a commodity elevator, a food processor under contract, a
cooperative pool, an export terminal, or a distillery directly.

Code prefix: damt_ (ag market - avoids collision with dam_ from domain_ag_method)
Categories: Commodity Market Channels, Contractual and Forward Sales,
Cooperative and Pooled Marketing, Direct and Local Market Channels,
Export and International Trade, Government and Program Channels.

Stakeholders: grain merchants, ag lenders calculating revenue streams,
farm managers timing sales, USDA AMS market news reporters, food companies
sourcing traceability.
Source: USDA AMS market data, CBOT/CME agricultural futures, USDA ERS
marketing margins. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AG_MARKET_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Commodity Market Channels --
    ("damt_commodity",        "Commodity Market Channels",                            1, None),
    ("damt_commodity_spot",   "Spot Cash Sale (local elevator, current price)",      2, "damt_commodity"),
    ("damt_commodity_futures","Exchange-Based Futures Hedge (CBOT, CME)",            2, "damt_commodity"),
    ("damt_commodity_basis",  "Basis Contract (futures price minus local basis)",    2, "damt_commodity"),

    # -- Contractual and Forward Sales --
    ("damt_contract",         "Contractual and Forward Sales",                        1, None),
    ("damt_contract_forward", "Forward Price Contract (fixed price before harvest)", 2, "damt_contract"),
    ("damt_contract_hta",     "Hedge-to-Arrive Contract (locks futures, open basis)", 2, "damt_contract"),
    ("damt_contract_mktg",    "Marketing Contract (price determined at delivery)",   2, "damt_contract"),
    ("damt_contract_prodxn",  "Production Contract (integrator sets price and specs)", 2, "damt_contract"),

    # -- Cooperative and Pooled Marketing --
    ("damt_coop",             "Cooperative and Pooled Marketing",                     1, None),
    ("damt_coop_grain",       "Grain Marketing Cooperative Pool",                    2, "damt_coop"),
    ("damt_coop_dairy",       "Dairy Cooperative (FMMO pool pricing)",               2, "damt_coop"),
    ("damt_coop_supply",      "Supply and Service Cooperative",                      2, "damt_coop"),

    # -- Direct and Local Market Channels --
    ("damt_direct",           "Direct and Local Market Channels",                     1, None),
    ("damt_direct_farm",      "Direct-to-Consumer (farmstand, CSA, u-pick)",         2, "damt_direct"),
    ("damt_direct_farmers",   "Farmers Market Sales",                                2, "damt_direct"),
    ("damt_direct_rest",      "Direct-to-Restaurant and Food Service",               2, "damt_direct"),
    ("damt_direct_online",    "Online Direct Sales (farm e-commerce, aggregators)",  2, "damt_direct"),

    # -- Export and International Trade --
    ("damt_export",           "Export and International Trade",                       1, None),
    ("damt_export_bulk",      "Bulk Commodity Export (FOB Gulf or Pacific terminal)", 2, "damt_export"),
    ("damt_export_container", "Containerized Export (specialty, organic, identity-preserved)", 2, "damt_export"),
    ("damt_export_fas",       "Foreign Agricultural Service (FAS) Program Sales",   2, "damt_export"),

    # -- Government and Program Channels --
    ("damt_govt",             "Government and Program Channels",                      1, None),
    ("damt_govt_ccc",         "USDA Commodity Credit Corporation (CCC) Loan",        2, "damt_govt"),
    ("damt_govt_snap",        "SNAP / Food Assistance Program Eligible Market",      2, "damt_govt"),
    ("damt_govt_school",      "USDA School Lunch and Nutrition Program Sales",       2, "damt_govt"),
]

_DOMAIN_ROW = (
    "domain_ag_market",
    "Agricultural Market Channel Types",
    "Agricultural market channel and sales type classification - commodity, "
    "forward contracts, cooperative, direct, export, and government channels",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["11"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific market channel types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ag_market(conn) -> int:
    """Ingest Agricultural Market Channel domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ag_market'), and links NAICS 11 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ag_market",
        "Agricultural Market Channel Types",
        "Agricultural market channel and sales type classification - commodity, "
        "forward contracts, cooperative, direct, export, and government channels",
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

    parent_codes = {parent for _, _, _, parent in AG_MARKET_NODES if parent is not None}

    rows = [
        (
            "domain_ag_market",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AG_MARKET_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AG_MARKET_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ag_market'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ag_market'",
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
            [("naics_2022", code, "domain_ag_market", "primary") for code in naics_codes],
        )

    return count
