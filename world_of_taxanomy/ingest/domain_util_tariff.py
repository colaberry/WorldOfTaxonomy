"""Utility Tariff and Rate Structure domain taxonomy ingester.

Classifies how utilities price electricity and gas delivery - orthogonal
to energy source and grid region. The same kWh of solar generation can be
billed under a residential flat rate, a TOU rate, a demand charge tariff
for commercial customers, a wholesale LMP rate for large industrials, or
a net metering credit for distributed generation.

Code prefix: dut_
Categories: Residential Rate Structures, Commercial and Industrial Tariffs,
Wholesale and Market-Based Rates, Distributed Generation and Net Metering,
Special Purpose Tariffs.

Stakeholders: utility rate case analysts, PUC commissioners, large industrial
rate negotiators, solar project developers calculating net metering value,
demand response aggregators.
Source: FERC electric tariff filings, NARUC rate design guidelines, NREL
utility tariff database, EIA electric power survey. Hand-coded.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
UTIL_TARIFF_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- Residential Rate Structures --
    ("dut_res",              "Residential Rate Structures",                     1, None),
    ("dut_res_flat",         "Flat / Tiered Energy Rate (cents per kWh)",      2, "dut_res"),
    ("dut_res_tou",          "Time-of-Use (TOU) Rate (peak/off-peak periods)", 2, "dut_res"),
    ("dut_res_cpp",          "Critical Peak Pricing (CPP) Rate",               2, "dut_res"),
    ("dut_res_budget",       "Budget Billing and Levelized Payment Plan",      2, "dut_res"),

    # -- Commercial and Industrial Tariffs --
    ("dut_comm",             "Commercial and Industrial Tariffs",               1, None),
    ("dut_comm_demand",      "Demand Charge Tariff ($/kW measured peak demand)", 2, "dut_comm"),
    ("dut_comm_tou",         "Commercial TOU with Demand and Energy Components", 2, "dut_comm"),
    ("dut_comm_interruptible","Interruptible Service Rate (curtailable load)",  2, "dut_comm"),
    ("dut_comm_rtp",         "Real-Time Pricing (industrial, hourly wholesale pass-through)", 2, "dut_comm"),
    ("dut_comm_economic",    "Economic Development / Large Load Attraction Rate", 2, "dut_comm"),

    # -- Wholesale and Market-Based Rates --
    ("dut_wholesale",        "Wholesale and Market-Based Rates",                1, None),
    ("dut_wholesale_lmp",    "Locational Marginal Price (LMP) - ISO/RTO Markets", 2, "dut_wholesale"),
    ("dut_wholesale_ppa",    "Power Purchase Agreement (PPA) - Fixed or Indexed", 2, "dut_wholesale"),
    ("dut_wholesale_capacity","Capacity Market Payment (ISO-NE, PJM, MISO)",   2, "dut_wholesale"),
    ("dut_wholesale_ancillary","Ancillary Services Market (spinning reserve, regulation)", 2, "dut_wholesale"),

    # -- Distributed Generation and Net Metering --
    ("dut_nem",              "Distributed Generation and Net Metering",         1, None),
    ("dut_nem_1",            "Net Energy Metering 1.0 (retail rate credit)",   2, "dut_nem"),
    ("dut_nem_2",            "Net Billing Tariff (export at avoided cost)",    2, "dut_nem"),
    ("dut_nem_vnem",         "Virtual Net Metering (shared solar, community)", 2, "dut_nem"),
    ("dut_nem_fita",         "Feed-In Tariff (FIT) - Guaranteed export rate",  2, "dut_nem"),

    # -- Special Purpose Tariffs --
    ("dut_special",          "Special Purpose and Incentive Tariffs",           1, None),
    ("dut_special_green",    "Green Tariff / Renewable Energy Tariff (REAT)",  2, "dut_special"),
    ("dut_special_ev",       "EV Charging Rate (time-of-use for transportation)", 2, "dut_special"),
    ("dut_special_lics",     "Low-Income Customer Assistance Program (CARE, FERA)", 2, "dut_special"),
    ("dut_special_dr",       "Demand Response Program Incentive Rate",         2, "dut_special"),
]

_DOMAIN_ROW = (
    "domain_util_tariff",
    "Utility Tariff and Rate Structure Types",
    "Utility tariff and rate structure classification - residential, commercial, "
    "wholesale, net metering, and special purpose tariffs",
    "WorldOfTaxanomy",
    None,
)

_NAICS_PREFIXES = ["22"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific tariff types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_util_tariff(conn) -> int:
    """Ingest Utility Tariff and Rate Structure domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_util_tariff'), and links NAICS 22 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_util_tariff",
        "Utility Tariff and Rate Structure Types",
        "Utility tariff and rate structure classification - residential, commercial, "
        "wholesale, net metering, and special purpose tariffs",
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

    parent_codes = {parent for _, _, _, parent in UTIL_TARIFF_NODES if parent is not None}

    rows = [
        (
            "domain_util_tariff",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in UTIL_TARIFF_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(UTIL_TARIFF_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_util_tariff'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_util_tariff'",
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
            [("naics_2022", code, "domain_util_tariff", "primary") for code in naics_codes],
        )

    return count
